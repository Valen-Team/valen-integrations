const {test} = require('node:test');
const assert = require('node:assert/strict');
const {Valen} = require('../dist/nodes/Valen/Valen.node');
const p = require('../dist/nodes/Valen/protocol');
function harness(params, replies, items=[{json:{ticket:'hello'},binary:{data:{mimeType:'image/png'}}}]) {
 const calls=[];
 const ctx={getInputData:()=>items,getNodeParameter:(key,i,fallback)=>params[key] ?? fallback,getCredentials:async()=>({baseUrl:'https://example.org/v1/',apiKey:'test-key'}),getNode:()=>({name:'Valen',type:'valen',typeVersion:1,position:[0,0],parameters:{}}),continueOnFail:()=>!!params.continue,
 helpers:{httpRequest:async request=>{calls.push(request); const reply=replies.shift(); if(reply instanceof Error) throw reply; return reply;},getBinaryDataBuffer:async()=>Buffer.from([137,80,78,71,13,10,26,10])}};
 return {ctx,calls,run:()=>new Valen().execute.call(ctx)};
}
const predicate=(probability)=>({model_id:'valen-2b-version',answers:[{name:'route',type:'predicate',probability}]});
const base={operation:'route',questionType:'predicate',question:'Urgent?',inputFormat:'text',input:'A synthetic ticket',model:'valen-2b'};
test('URL and option normalization, duplicate and invalid input rejection',()=>{
 for(const url of ['https://example.org','https://example.org/','https://example.org/v1/']) assert.equal(p.baseUrl(url),'https://example.org/v1');
 assert.throws(()=>p.baseUrl('file:///tmp/a'));
 assert.deepEqual(p.options('billing: Payments: duplicate charge\n\ntech'),[{value:'billing',description:'Payments: duplicate charge'},{value:'tech',description:'tech'}]);
 assert.throws(()=>p.options('x\nx')); assert.throws(()=>p.questions('[]'));
 assert.throws(()=>p.questions([{name:'x',type:'predicate',instructions:''}]));
});
test('Yes/No boundary and uncertain items use correct ports, preserving pairing',async()=>{
 const h=harness(base,[predicate(.7),predicate(.3),predicate(.5)],[{json:{id:1}},{json:{id:2}},{json:{id:3}}]);
 const out=await h.run(); assert.deepEqual(out.map(port=>port[0].json.valen.branch),['yes','no','unsure']);
 assert.deepEqual(out.map(port=>port[0].pairedItem.item),[0,1,2]);
 assert.equal(out[0][0].json.id,1); assert.equal(out[0][0].json.valen.model,'valen-2b-version');
 assert.equal(h.calls[0].headers.Authorization,'Bearer test-key'); assert.equal(h.calls[0].url,'https://example.org/v1/decisions');
});
test('Evaluate batches questions, serializes JSON, preserves binary',async()=>{
 const h=harness({operation:'evaluate',inputFormat:'json',input:'{"问":"好"}',questions:'[{"name":"q","type":"predicate","instructions":"Test"}]',model:'valen-2b',imageField:'data'},[{model:'valen',answers:[{name:'q',type:'predicate',probability:.2}]}]);
 const out=await h.run(); assert.equal(out[0][0].json.valen.answers.q.probability,.2);
 assert.equal(h.calls[0].body.input[0].content[0].text,'{\n  "问": "好"\n}');
 assert.match(h.calls[0].body.input[0].content[1].image_url,/^data:image\/png;base64,/);
 assert.ok(out[0][0].binary.data);
});
test('Choice routing follows configured order',async()=>{
 const h=harness({...base,questionType:'choice',options:'billing: Payments\ntech: Software'},[{model:'v',answers:[{name:'route',type:'choice',choice:'tech',confidence:.8,probabilities:[{value:'billing',probability:.1},{value:'tech',probability:.9}]}]}]);
 const out=await h.run(); assert.equal(out[0].length,0); assert.equal(out[1][0].json.valen.branch,'tech');
});
test('Unsupported image metadata stops before inference',async()=>{
 const h=harness({...base,imageField:'data'},[],[{json:{},binary:{data:{mimeType:'image/gif'}}}]);
 await assert.rejects(h.run(),/PNG, JPEG or WebP/);
 assert.equal(h.calls.length,0);
});
test('Score routes by most likely label, lower label on ties (not rounded expectation)',async()=>{
 const h=harness({...base,questionType:'score',options:'low\nmedium\nhigh'},[{model:'v',answers:[{name:'route',type:'score',score:1,confidence:0,probabilities:[{label:'low',probability:.5},{label:'medium',probability:0},{label:'high',probability:.5}]}]}]);
 const out=await h.run(); assert.equal(out[0][0].json.valen.branch,'low');
});
test('Bad thresholds stop before any API call',async()=>{
 const h=harness({...base,yesAt:.2,noAt:.7},[]); await assert.rejects(h.run(),/Thresholds/); assert.equal(h.calls.length,0);
});
test('Missing or malformed answers fail closed',async()=>{
 for(const response of [{model:'v',answers:[]},predicate(NaN),predicate(1.2)]) await assert.rejects(harness(base,[response]).run());
});
test('Permanent errors are not retried and preserve request ID',async()=>{
 const e=Object.assign(new Error('bad'),{statusCode:400,response:{body:{detail:'Invalid question'},headers:{'x-request-id':'req-123'}}});
 const h=harness(base,[e]); await assert.rejects(h.run(),/400: Invalid question.*req-123/); assert.equal(h.calls.length,1);
});
test('Hosted question limit is reported by the API, not imposed on self-hosted servers',async()=>{
 const asked=Array.from({length:9},(_,i)=>({name:'q'+i,type:'predicate',instructions:'Synthetic judgment'}));
 const e=Object.assign(new Error('bad'),{statusCode:400,response:{body:{detail:'At most 8 questions'},headers:{'x-request-id':'limit-123'}}});
 const h=harness({...base,operation:'evaluate',questions:asked},[e]);
 await assert.rejects(h.run(),/400: At most 8 questions.*limit-123/);
 assert.equal(h.calls[0].body.questions.length,9);
 assert.equal(h.calls.length,1);
});
test('Transient failures retry, continue-on-error carries no answer',async()=>{
 const e=Object.assign(new Error('unavailable'),{statusCode:503});
 const h=harness(base,[e,predicate(.8)]); assert.equal((await h.run())[0].length,1); assert.equal(h.calls.length,2);
 const failed=await harness({...base,continue:true},[new Error('offline')]).run();
 assert.match(failed[2][0].json.error,/offline/); assert.equal(failed[2][0].json.details.input.ticket,'hello'); assert.equal(failed[2][0].json.valen,undefined);
});
test('Model discovery filters Valen IDs',async()=>{
 const h=harness({},[{data:[{id:'valen-4b'},{id:'another'}]}]);
 assert.deepEqual(await new Valen().methods.loadOptions.getModels.call(h.ctx),[{name:'valen-4b',value:'valen-4b'}]);
});
test('Axios timeout errors retry with the same per-attempt timeout',async()=>{
 const timeout=Object.assign(new Error('timeout of 120000ms exceeded'),{code:'ECONNABORTED'});
 const h=harness(base,[timeout,timeout,predicate(.8)]);
 assert.equal((await h.run())[0][0].json.valen.branch,'yes');
 assert.equal(h.calls.length,3);
 assert.ok(h.calls.every(call=>call.timeout===120000));
});
test('Node exports declare package metadata and route port names',()=>{
 const pkg=require('../package.json'); assert.equal(pkg.n8n.nodes[0],'dist/nodes/Valen/Valen.node.js');
 const d=new Valen().description;
 const evaluate=(expression,params)=>Function('$parameter',`return (${expression.slice(3,-2)})`)(params);
 assert.deepEqual(evaluate(d.outputs,base).map(p=>p.displayName),['yes','no','unsure']);
 assert.deepEqual(evaluate(d.outputs,{operation:'route',questionType:'choice',options:'billing: Payments\ntech'}).map(p=>p.displayName),['billing','tech']);
 assert.deepEqual(evaluate(d.outputs,{operation:'evaluate'}),[{type:'main',displayName:'Output'}]);
});
test('n8n expression engine resolves real output ports and credential URL',()=>{
 const {Workflow,NodeHelpers}=require('n8n-workflow');
 const nodeType=new Valen();
 const node={id:'v',name:'Valen',type:'valen',typeVersion:1,position:[0,0],parameters:{...base,questionType:'choice',options:'billing: Payments\ntech'}};
 const workflow=new Workflow({nodes:[node],connections:{},active:false,nodeTypes:{getByNameAndVersion:()=>nodeType,getKnownTypes:()=>({})}});
 assert.deepEqual(NodeHelpers.getNodeOutputs(workflow,node,nodeType.description).map(p=>p.displayName),['billing','tech']);
 const {ValenApi}=require('../dist/credentials/ValenApi.credentials');
 const credentials=new ValenApi();
 // The credential test expression is evaluated using n8n's own expression parser.
 const url=workflow.expression.getSimpleParameterValue(node,credentials.test.request.baseURL,'internal',{$credentials:{baseUrl:'https://example.org/v1/'}});
 assert.equal(url,'https://example.org/v1');
});
