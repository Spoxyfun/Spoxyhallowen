// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/**
 * Spooky Halloween (SPOOKY) — BNB Chain
 *
 * Koleksi 10.000 NFT pixel dalam SATU pool bersama (#1–#10.000):
 *  - mintFree(qty): NFT gratis, hanya membayar fee 0,0001 BNB per mint.
 *  - mintPaid(qty): 0,001 BNB per NFT.
 * Keduanya mengundi token secara acak dari token yang belum ter-mint
 * di pool yang sama (lazy Fisher-Yates / swap-with-last). Nomor token
 * tidak bisa dipilih dan tidak pernah terundi dua kali.
 *
 * File ini mandiri (tanpa import eksternal) supaya bisa langsung
 * di-compile & deploy dari Remix (https://remix.ethereum.org):
 *   1. Compile dengan Solidity 0.8.20+ (optimizer ON, runs 200).
 *   2. Deploy di jaringan BNB Chain (chainId 56) dari wallet owner.
 *   3. Panggil setBaseURI("https://spoxydev.fun/metadata/").
 *   4. Panggil setMintOpen(true) untuk membuka mint.
 *   5. Tempel alamat kontrak ke konstanta CONTRACT_ADDRESS di index.html.
 *
 * CATATAN KEAMANAN: undian memakai block.prevrandao / blockhash /
 * timestamp sebagai sumber acak on-chain. Itu cukup untuk undian
 * koleksi bernilai kecil seperti ini, tetapi BUKAN randomness yang
 * tahan manipulasi validator (bukan VRF). Jangan gunakan pola ini
 * untuk undian bernilai besar tanpa mengganti sumber acaknya.
 */

interface IERC165 {
    function supportsInterface(bytes4 interfaceId) external view returns (bool);
}

interface IERC721Receiver {
    function onERC721Received(address operator, address from, uint256 tokenId, bytes calldata data)
        external
        returns (bytes4);
}

contract SpookyHalloween is IERC165 {
    // ------------------------------------------------------------------
    // ERC-721 metadata
    // ------------------------------------------------------------------
    string public constant name = "Spooky Halloween";
    string public constant symbol = "SPOOKY";

    // ------------------------------------------------------------------
    // Konfigurasi koleksi (sesuai yang dijanjikan di situs)
    // ------------------------------------------------------------------
    uint256 public constant MAX_SUPPLY = 10_000;
    uint256 public constant FREE_FEE = 0.0001 ether; // per NFT, mintFree
    uint256 public constant PAID_PRICE = 0.001 ether; // per NFT, mintPaid
    uint256 public constant MAX_PER_TX = 10; // sama dengan batas stepper di situs

    address public owner;
    bool public mintOpen;
    string private _baseTokenURI;

    // Pool undian: posisi 0.._remaining-1 masih berisi token belum ter-mint.
    // _pool[i] == 0 berarti posisi i masih memegang tokenId i+1 (default).
    mapping(uint256 => uint256) private _pool;
    uint256 private _remaining = MAX_SUPPLY;
    uint256 private _minted;
    uint256 private _nonce;

    // ERC-721 state
    mapping(uint256 => address) private _owners;
    mapping(address => uint256) private _balances;
    mapping(uint256 => address) private _tokenApprovals;
    mapping(address => mapping(address => bool)) private _operatorApprovals;

    bool private _locked;

    // ------------------------------------------------------------------
    // Events
    // ------------------------------------------------------------------
    event Transfer(address indexed from, address indexed to, uint256 indexed tokenId);
    event Approval(address indexed owner_, address indexed approved, uint256 indexed tokenId);
    event ApprovalForAll(address indexed owner_, address indexed operator, bool approved);
    event SpookyMinted(address indexed minter, uint256 indexed tokenId, bool paid);
    event MintOpenChanged(bool open);
    event BaseURIChanged(string baseURI);
    event Withdrawal(address indexed to, uint256 amount);
    event OwnershipTransferred(address indexed previousOwner, address indexed newOwner);

    modifier onlyOwner() {
        require(msg.sender == owner, "SPOOKY: not owner");
        _;
    }

    modifier nonReentrant() {
        require(!_locked, "SPOOKY: reentrant");
        _locked = true;
        _;
        _locked = false;
    }

    constructor() {
        owner = msg.sender;
        emit OwnershipTransferred(address(0), msg.sender);
    }

    // ------------------------------------------------------------------
    // Mint
    // ------------------------------------------------------------------
    function mintFree(uint256 qty) external payable nonReentrant returns (uint256[] memory tokenIds) {
        return _mint(qty, FREE_FEE * qty, false);
    }

    function mintPaid(uint256 qty) external payable nonReentrant returns (uint256[] memory tokenIds) {
        return _mint(qty, PAID_PRICE * qty, true);
    }

    function _mint(uint256 qty, uint256 cost, bool paid) internal returns (uint256[] memory tokenIds) {
        require(mintOpen, "SPOOKY: mint not open");
        require(qty > 0 && qty <= MAX_PER_TX, "SPOOKY: qty 1-10");
        require(msg.value == cost, paid ? "SPOOKY: send exact paid price" : "SPOOKY: send exact free fee");
        require(_remaining >= qty, "SPOOKY: pool empty");

        tokenIds = new uint256[](qty);
        for (uint256 i = 0; i < qty; i++) {
            uint256 tokenId = _draw();
            tokenIds[i] = tokenId;
            _owners[tokenId] = msg.sender;
            _balances[msg.sender] += 1;
            emit Transfer(address(0), msg.sender, tokenId);
            emit SpookyMinted(msg.sender, tokenId, paid);
            _checkOnERC721Received(address(0), msg.sender, tokenId, "");
        }
    }

    /// @dev Ambil satu token acak dari pool, lalu tukar dengan token
    ///      terakhir yang tersisa supaya tidak bisa terundi lagi.
    function _draw() internal returns (uint256 tokenId) {
        uint256 remainingBefore = _remaining;
        uint256 idx = _random(remainingBefore);
        tokenId = _pool[idx] == 0 ? idx + 1 : _pool[idx];
        uint256 lastId = _pool[remainingBefore - 1] == 0 ? remainingBefore : _pool[remainingBefore - 1];
        _pool[idx] = lastId;
        _remaining = remainingBefore - 1;
        _minted += 1;
    }

    function _random(uint256 bound) internal returns (uint256) {
        _nonce += 1;
        bytes32 hash = keccak256(
            abi.encodePacked(
                block.prevrandao, blockhash(block.number - 1), block.timestamp, block.number, msg.sender, address(this), _nonce, bound
            )
        );
        return uint256(hash) % bound;
    }

    // ------------------------------------------------------------------
    // Status pool
    // ------------------------------------------------------------------
    function totalMinted() external view returns (uint256) {
        return _minted;
    }

    function remaining() external view returns (uint256) {
        return _remaining;
    }

    // ------------------------------------------------------------------
    // Owner
    // ------------------------------------------------------------------
    function setMintOpen(bool open_) external onlyOwner {
        mintOpen = open_;
        emit MintOpenChanged(open_);
    }

    function setBaseURI(string calldata baseURI_) external onlyOwner {
        _baseTokenURI = baseURI_;
        emit BaseURIChanged(baseURI_);
    }

    function baseURI() external view returns (string memory) {
        return _baseTokenURI;
    }

    function withdraw() external onlyOwner nonReentrant {
        uint256 amount = address(this).balance;
        require(amount > 0, "SPOOKY: nothing to withdraw");
        (bool ok, ) = payable(owner).call{value: amount}("");
        require(ok, "SPOOKY: withdraw failed");
        emit Withdrawal(owner, amount);
    }

    function transferOwnership(address newOwner) external onlyOwner {
        require(newOwner != address(0), "SPOOKY: zero address");
        emit OwnershipTransferred(owner, newOwner);
        owner = newOwner;
    }

    // ------------------------------------------------------------------
    // ERC-721
    // ------------------------------------------------------------------
    function tokenURI(uint256 tokenId) external view returns (string memory) {
        require(_owners[tokenId] != address(0), "SPOOKY: token not minted");
        return string(abi.encodePacked(_baseTokenURI, _toString(tokenId), ".json"));
    }

    function balanceOf(address account) external view returns (uint256) {
        require(account != address(0), "SPOOKY: zero address");
        return _balances[account];
    }

    function ownerOf(uint256 tokenId) external view returns (address) {
        address tokenOwner = _owners[tokenId];
        require(tokenOwner != address(0), "SPOOKY: token not minted");
        return tokenOwner;
    }

    function approve(address to, uint256 tokenId) external {
        address tokenOwner = _owners[tokenId];
        require(tokenOwner != address(0), "SPOOKY: token not minted");
        require(msg.sender == tokenOwner || _operatorApprovals[tokenOwner][msg.sender], "SPOOKY: not authorized");
        _tokenApprovals[tokenId] = to;
        emit Approval(tokenOwner, to, tokenId);
    }

    function getApproved(uint256 tokenId) external view returns (address) {
        require(_owners[tokenId] != address(0), "SPOOKY: token not minted");
        return _tokenApprovals[tokenId];
    }

    function setApprovalForAll(address operator, bool approved) external {
        _operatorApprovals[msg.sender][operator] = approved;
        emit ApprovalForAll(msg.sender, operator, approved);
    }

    function isApprovedForAll(address account, address operator) external view returns (bool) {
        return _operatorApprovals[account][operator];
    }

    function transferFrom(address from, address to, uint256 tokenId) public {
        _transfer(from, to, tokenId);
    }

    function safeTransferFrom(address from, address to, uint256 tokenId) external {
        _transfer(from, to, tokenId);
        _checkOnERC721Received(from, to, tokenId, "");
    }

    function safeTransferFrom(address from, address to, uint256 tokenId, bytes calldata data) external {
        _transfer(from, to, tokenId);
        _checkOnERC721Received(from, to, tokenId, data);
    }

    function _transfer(address from, address to, uint256 tokenId) internal {
        address tokenOwner = _owners[tokenId];
        require(tokenOwner == from, "SPOOKY: wrong from");
        require(to != address(0), "SPOOKY: zero address");
        require(
            msg.sender == from || msg.sender == _tokenApprovals[tokenId] || _operatorApprovals[from][msg.sender],
            "SPOOKY: not authorized"
        );
        delete _tokenApprovals[tokenId];
        _balances[from] -= 1;
        _balances[to] += 1;
        _owners[tokenId] = to;
        emit Transfer(from, to, tokenId);
    }

    function supportsInterface(bytes4 interfaceId) external pure returns (bool) {
        return interfaceId == 0x01ffc9a7 // ERC165
            || interfaceId == 0x80ac58cd // ERC721
            || interfaceId == 0x5b5e139f; // ERC721Metadata
    }

    // ------------------------------------------------------------------
    // Helpers
    // ------------------------------------------------------------------
    function _checkOnERC721Received(address from, address to, uint256 tokenId, bytes memory data) internal {
        if (to.code.length > 0) {
            try IERC721Receiver(to).onERC721Received(msg.sender, from, tokenId, data) returns (bytes4 retval) {
                require(retval == IERC721Receiver.onERC721Received.selector, "SPOOKY: receiver rejected");
            } catch {
                revert("SPOOKY: receiver rejected");
            }
        }
    }

    function _toString(uint256 value) internal pure returns (string memory) {
        if (value == 0) return "0";
        uint256 temp = value;
        uint256 digits;
        while (temp != 0) {
            digits++;
            temp /= 10;
        }
        bytes memory buffer = new bytes(digits);
        while (value != 0) {
            digits -= 1;
            buffer[digits] = bytes1(uint8(48 + uint256(value % 10)));
            value /= 10;
        }
        return string(buffer);
    }
}
