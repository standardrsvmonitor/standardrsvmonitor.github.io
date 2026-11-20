// Run against the generated page, with deterministic source responses and a fixed clock.
async function checkInvestorDashboard() {
  const results = {};
  const original = {fetch: window.fetch, now: Date.now, warn: console.warn};
  const t = DATA.tipTs, b = DATA.tip+1;
  const bank = {totalBranches:L.branches, multiplierWad:'1000000000000000000', epochNumber:L.epoch,
    epochStart:L.epochStart, epochEnd:L.epochEnd, totalPendingLive:'1000000000000000000', cumulativeIssued:'1000000000000000000'};
  const snapshot = {blockNumber:b, blockTimestamp:t, bank, tax:{epochNetFlow:'0'}, token:{burnedForever:'0', maxSupply:'1000000000000000000000000000'}};
  let fault = '';
  const response = (data,status=200)=>({ok:status===200,status,json:async()=>data});
  const amounts=[L.totalSupply,L.poolStd,L.incentivesStd,L.sbillsStd,L.teamStd,L.burnedForever,L.maxSupply,L.teamEth]
    .map(n=>'0x'+BigInt(Math.round(n*1e18)).toString(16));
  const baseline = JSON.stringify(BASE.row);
  const initialBuffer = owedBuf[BASE.row.date];
  const status = ()=>document.querySelector('#status').textContent;
  const clean = ()=>!LIVE && L.price===BASE.L.price && JSON.stringify(Sh.at(-1))===baseline && !updating;
  try {
    Date.now=()=>t*1000;
    console.warn=(...a)=>{if(a[0]!=='Live update unavailable') original.warn(...a);};
    window.fetch=async(url,options)=>{
      if(url===RPCU) return response(JSON.parse(options.body).map((call,i)=>({id:i,result:call.method==='eth_getLogs'?[]:amounts[i]})));
      if(url.includes('home?')) {
        const liveBank={...bank,epochNumber:bank.epochNumber+(fault==='settlement'?1:0)};
        if(fault==='missing pending claims') delete liveBank.totalPendingLive;
        if(fault==='malformed multiplier') liveBank.multiplierWad='12units';
        return response({snapshot:{...snapshot,blockTimestamp:fault==='midnight'?t+86400:t,bank:liveBank}});
      }
      if(url.includes('dexscreener')) return response([{pairAddress:'0xc73f3cd3fb68288e63f008e08ef69caa0437224e420963c6aeb4526178e87ad9',priceUsd:2}]);
      if(url.includes('leaderboard')) return response({bankers:[{owner:A.teamWallet,branches:L.branches}]});
      if(url.includes('sbills/history')) return response({asOf:{blockTimestamp:t-(fault==='stale bills'?2000:0)},current:{locked:'0',rate:'0',principal:'0'}});
      if(!url.includes('activity?')) throw new Error('Unexpected QA request');
      const withdrawal=url.includes('kind=withdrawn');
      if(withdrawal && fault==='HTTP error') return response({error:'unavailable'},503);
      if(withdrawal && fault==='invalid page') return response({events:[]});
      const event={blockNumber:b,timestamp:t,values:{gross:'110000000000000000000',net:'100000000000000000000'},txHash:'0x1234',logIndex:1};
      return response({events:withdrawal?[event]:[],page:{nextCursor:withdrawal&&fault==='repeated cursor'?'repeat':null}});
    };
    const fixture={fee:.01,taxSell:.03,slip:[
      {usd:100000,sellFillable:true,sellAllIn:.06},{usd:250000,sellFillable:false,sellAllIn:null},{usd:500000,sellAllIn:.25}]};
    renderSaleQuote(fixture,null,123,2000);
    const size=document.getElementById('sale_size'), payout=document.getElementById('sale_out');
    const select=value=>{ size.value=String(value); size.dispatchEvent(new Event('change')); return payout.textContent; };
    const full=payout.textContent==='$94,000 · 47.00 ETH';
    const exceeds=select(250000)==='Exceeds pool liquidity', unknown=select(500000)==='Estimate unavailable';
    renderSaleQuote(null,null,123,2000);
    results['sale-size picker handles fill status']=full && exceeds && unknown && size.disabled && payout.textContent==='Estimate unavailable';
    renderSaleQuote(DATA.depth,DATA.billSchedule,DATA.tip,BASE.L.ethusd);
    await goLive();
    results['successful replay updates state and recycled claims'] = LIVE && L.price===2 &&
      Math.abs(owedBuf[BASE.row.date] - (initialBuffer+5))<0.001;
    for(const scenario of ['missing pending claims','malformed multiplier','HTTP error','invalid page','repeated cursor','stale bills','midnight','settlement']){
      fault=scenario; await goLive();
      results[scenario+' restores the compiled view']=clean() && status().includes('Compiled') && status().includes('unavailable');
    }
  } finally {
    window.fetch=original.fetch; Date.now=original.now; console.warn=original.warn;
    restore(); LIVE=false; LIVEB=0; LIVE_ERROR=false; NOWTS=DATA.pulledAt; renderAll(); redrawAll();
  }
  return results;
}
