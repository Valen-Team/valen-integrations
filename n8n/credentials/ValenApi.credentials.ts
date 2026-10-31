import type { ICredentialType, INodeProperties, IAuthenticateGeneric, ICredentialTestRequest } from 'n8n-workflow';

export class ValenApi implements ICredentialType {
 name = 'valenApi';
 displayName = 'Valen API';
 documentationUrl = 'https://valen-team.github.io/docs/valen/api/';
 properties: INodeProperties[] = [
  { displayName: 'Base URL', name: 'baseUrl', type: 'string', default: 'https://api.valen-team.workers.dev', required: true },
  { displayName: 'API Key', name: 'apiKey', type: 'string', typeOptions: { password: true }, default: '', description: 'Leave empty for the free API. Use a key for the keyed or your own deployment.' },
 ];
 authenticate: IAuthenticateGeneric = { type: 'generic', properties: { headers: {
  Authorization: '={{$credentials.apiKey ? "Bearer " + $credentials.apiKey : ""}}',
  'User-Agent': 'valen-n8n/0.1.0',
 } } };
 test: ICredentialTestRequest = { request: {
  baseURL: '={{$credentials.baseUrl.replace(/\\/+$/, "").replace(/\\/v1$/, "") + "/v1"}}',
  url: '/models', method: 'GET', timeout: 120000,
 } };
}
