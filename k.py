# minimal keccak-256 (pure python) for event topics / selectors
RC=[0x0000000000000001,0x0000000000008082,0x800000000000808A,0x8000000080008000,0x000000000000808B,0x0000000080000001,0x8000000080008081,0x8000000000008009,0x000000000000008A,0x0000000000000088,0x0000000080008009,0x000000008000000A,0x000000008000808B,0x800000000000008B,0x8000000000008089,0x8000000000008003,0x8000000000008002,0x8000000000000080,0x000000000000800A,0x800000008000000A,0x8000000080008081,0x8000000000008080,0x0000000080000001,0x8000000080008008]
ROT=[[0,36,3,41,18],[1,44,10,45,2],[62,6,43,15,61],[28,55,25,21,56],[27,20,39,8,14]]
M=(1<<64)-1
def _f(st):
    for rc in RC:
        C=[st[x][0]^st[x][1]^st[x][2]^st[x][3]^st[x][4] for x in range(5)]
        D=[C[(x-1)%5]^(((C[(x+1)%5]<<1)|(C[(x+1)%5]>>63))&M) for x in range(5)]
        st=[[st[x][y]^D[x] for y in range(5)] for x in range(5)]
        B=[[0]*5 for _ in range(5)]
        for x in range(5):
            for y in range(5):
                r=ROT[x][y]; v=st[x][y]; B[y][(2*x+3*y)%5]=((v<<r)|(v>>(64-r)))&M if r else v
        st=[[B[x][y]^((~B[(x+1)%5][y])&B[(x+2)%5][y]) for y in range(5)] for x in range(5)]
        st[0][0]^=rc
    return st
def keccak(data:bytes)->bytes:
    rate=136; st=[[0]*5 for _ in range(5)]
    d=bytearray(data); d.append(0x01)
    while len(d)%rate: d.append(0)
    d[-1]|=0x80
    for off in range(0,len(d),rate):
        blk=d[off:off+rate]
        for i in range(rate//8):
            st[i%5][i//5]^=int.from_bytes(blk[8*i:8*i+8],'little')
        st=_f(st)
    out=b''
    for i in range(4): out+=st[i%5][i//5].to_bytes(8,'little')
    return out
if __name__=="__main__":
    assert keccak(b"Transfer(address,address,uint256)").hex()=="ddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"
    assert keccak(b"Swap(bytes32,address,int128,int128,uint160,uint128,int24,uint24)").hex()=="40e9cecb9f5f1f1c5b9c97dec2917b7ee92e57ba5563708daca94dd84ad7112f"
    print("keccak ok", keccak(b"getSlot0(bytes32)").hex()[:8], keccak(b"ownerOf(uint256)").hex()[:8])
