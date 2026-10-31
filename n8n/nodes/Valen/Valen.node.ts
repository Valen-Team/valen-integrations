import { NodeConnectionTypes, NodeOperationError } from 'n8n-workflow';
import type { IExecuteFunctions, ILoadOptionsFunctions, INodeExecutionData, INodeType, INodeTypeDescription } from 'n8n-workflow';
import { answers, baseUrl, imageMime, options, questions, route, Question } from './protocol';

async function request(ctx: IExecuteFunctions | ILoadOptionsFunctions, method: 'GET' | 'POST', path: string, body?: object): Promise<any> {
 const credentials = await ctx.getCredentials('valenApi');
 const headers: Record<string,string> = {'User-Agent':'valen-n8n/0.1.0'};
 if (credentials.apiKey) headers.Authorization = `Bearer ${credentials.apiKey}`;
 for (let attempt = 0; ; attempt++) {
  try {
   return await ctx.helpers.httpRequest({method, url: baseUrl(String(credentials.baseUrl)) + path, headers, ...(body ? {body} : {}), json:true, timeout:120000});
  } catch (error: any) {
   const status = error.statusCode ?? error.response?.status ?? error.response?.statusCode;
   if (attempt < 2 && ([429,502,503,504].includes(Number(status)) || (!status && ['ECONNRESET','ECONNREFUSED','ETIMEDOUT','ECONNABORTED','EAI_AGAIN','ENOTFOUND','ESOCKETTIMEDOUT'].includes(error.code)))) {
    await new Promise(resolve => setTimeout(resolve, 250 * 2 ** attempt)); continue;
   }
   const payload = error.response?.body ?? error.response?.data ?? error.error;
   const detail = payload?.error?.message ?? payload?.detail ?? error.message;
   const message = typeof detail === 'string' ? detail : JSON.stringify(detail);
   const h = error.response?.headers ?? {};
   const id = h['x-request-id'] ?? h['x-llm-proxy-request-id'];
   throw new Error(`Valen ${status ?? 'connection error'}: ${message}${id ? ` (request ${id})` : ''}${Number(status) === 429 ? '. Wait at least a minute before retrying.' : ''}`);
  }
 }
}

export class Valen implements INodeType {
 description: INodeTypeDescription = {
  displayName:'Valen', name:'valen', icon:'file:valen.png', group:['transform'], version:1,
  description:'Ask typed questions about text or an image and route by the answers', defaults:{name:'Valen'},
  inputs:[NodeConnectionTypes.Main],
  outputs:'={{($parameter.operation === "evaluate" ? ["Output"] : ($parameter.questionType === "predicate" ? ["yes", "no", "unsure"] : ($parameter.options || "").split("\\n").filter(x => x.trim()).map(x => x.split(": ")[0].trim()))).map(displayName => ({type: "main", displayName}))}}',
  credentials:[{name:'valenApi',required:true}],
  properties:[
   {displayName:'Operation',name:'operation',type:'options',noDataExpression:true,default:'evaluate',options:[{name:'Evaluate',value:'evaluate',action:'Evaluate questions'},{name:'Route',value:'route',action:'Route by an answer'}]},
   {displayName:'Model Name or ID',name:'model',type:'options',typeOptions:{loadOptionsMethod:'getModels'},default:'valen-2b',required:true,description:'Hosted model ID or the name of your self-hosted model'},
   {displayName:'Input Format',name:'inputFormat',type:'options',default:'text',options:[{name:'Text',value:'text'},{name:'JSON',value:'json'},{name:'Input Item',value:'item'}]},
   {displayName:'Input',name:'input',type:'string',typeOptions:{rows:4},default:'',displayOptions:{hide:{inputFormat:['item']}}},
   {displayName:'Image Binary Field',name:'imageField',type:'string',default:'',description:'Optional binary property from an earlier node, for example data. One PNG, JPEG or WebP.'},
   {displayName:'Questions (JSON)',name:'questions',type:'json',default:'[{"name":"urgent","type":"predicate","instructions":"The customer needs urgent help."}]',displayOptions:{show:{operation:['evaluate']}},description:'Decisions API array of 1–8 named questions'},
   {displayName:'Question Type',name:'questionType',type:'options',noDataExpression:true,default:'predicate',options:[{name:'Yes/No',value:'predicate'},{name:'Choice',value:'choice'},{name:'Score',value:'score'}],displayOptions:{show:{operation:['route']}}},
   {displayName:'Question',name:'question',type:'string',typeOptions:{rows:3},default:'',required:true,displayOptions:{show:{operation:['route']}}},
   {displayName:'Options / Levels',name:'options',type:'string',noDataExpression:true,typeOptions:{rows:5},default:'',displayOptions:{show:{operation:['route'],questionType:['choice','score']}},description:'2–16 distinct lines: value or value: description. Score levels go lowest first. These define the output ports.'},
   {displayName:'Yes At',name:'yesAt',type:'number',default:0.7,typeOptions:{minValue:0,maxValue:1},displayOptions:{show:{operation:['route'],questionType:['predicate']}}},
   {displayName:'No At',name:'noAt',type:'number',default:0.3,typeOptions:{minValue:0,maxValue:1},displayOptions:{show:{operation:['route'],questionType:['predicate']}}},
  ],
 };
 methods = {loadOptions:{async getModels(this: ILoadOptionsFunctions) {
  const response = await request(this,'GET','/models');
  return (response.data ?? []).filter((m: any) => typeof m.id === 'string' && m.id.startsWith('valen')).map((m: any) => ({name:m.id,value:m.id}));
 }}};
 async execute(this: IExecuteFunctions): Promise<INodeExecutionData[][]> {
  const items = this.getInputData();
  const operation = this.getNodeParameter('operation',0) as string;
  const type = this.getNodeParameter('questionType',0,'predicate') as string;
  // Output ports are fixed for the whole node, not computed separately per item.
  const entries = operation === 'route' && type !== 'predicate' ? options(String(this.getNodeParameter('options',0))) : [];
  const labels = operation === 'evaluate' ? ['Output'] : type === 'predicate' ? ['yes','no','unsure'] : entries.map(r => r.value);
  const output: INodeExecutionData[][] = labels.map(() => []);
  for (let i=0; i<items.length; i++) {
   try {
    let asked: Question[];
    if (operation === 'evaluate') asked = questions(this.getNodeParameter('questions',i));
    else {
     const q: Question = {name:'route',type,instructions:this.getNodeParameter('question',i) as string};
     if (type === 'choice') q.choices = entries;
     if (type === 'score') q.levels = entries.map(r => ({label:r.value,description:r.description}));
     asked = questions([q]);
     route({probability:0,choice:labels[0],level:labels[0]},type,labels,Number(this.getNodeParameter('yesAt',i,0.7)),Number(this.getNodeParameter('noAt',i,0.3)));
    }
    const format = this.getNodeParameter('inputFormat',i) as string;
    const raw = format === 'item' ? items[i].json : this.getNodeParameter('input',i,'');
    let input: any = format === 'text' ? String(raw) : JSON.stringify(format === 'json' && typeof raw === 'string' ? JSON.parse(raw) : raw,null,2);
    if (format === 'json') { const parsed = JSON.parse(input); if (parsed === null || typeof parsed !== 'object') throw new Error('JSON input must be an object or array'); }
    const field = (this.getNodeParameter('imageField',i,'') as string).trim();
    if (field) {
     const declaredMime = items[i].binary?.[field]?.mimeType;
     if (declaredMime && !['image/png','image/jpeg','image/webp'].includes(declaredMime)) throw new Error('Image must be PNG, JPEG or WebP');
     const bytes = await this.helpers.getBinaryDataBuffer(i,field);
     const mime = imageMime(bytes);
     input = [{role:'user',content:[{type:'input_text',text:input},{type:'input_image',image_url:`data:${mime};base64,${bytes.toString('base64')}`}]}];
    }
    const response = await request(this,'POST','/decisions',{model:this.getNodeParameter('model',i),input,questions:asked});
    const mapped = answers(response,asked);
    const model = response.model_id ?? response.model;
    if (typeof model !== 'string' || !model) throw new Error('API returned no model ID');
    let index = 0;
    let valen: any = {answers:mapped,model};
    if (operation === 'route') {
     const selected = route(mapped.route,type,labels,Number(this.getNodeParameter('yesAt',i,0.7)),Number(this.getNodeParameter('noAt',i,0.3)));
     index = selected.index; valen = {...mapped.route,branch:selected.branch,model};
    }
    output[index].push({json:{...items[i].json,valen},binary:items[i].binary,pairedItem:{item:i}});
   } catch (error: any) {
    if (!this.continueOnFail()) throw new NodeOperationError(this.getNode(),error,{itemIndex:i});
    // Preserve failure explicitly; never manufacture a model judgment.
    // n8n normalizes a top-level item.error by replacing its JSON. Use its
    // error-only JSON envelope instead, preserving the source under details.
    output[operation === 'route' && type === 'predicate' ? 2 : 0].push({
     json:{error:error.message,details:{input:items[i].json}},
     binary:items[i].binary,pairedItem:{item:i},
    });
   }
  }
  return output;
 }
}
