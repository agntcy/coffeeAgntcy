from flask import Flask, jsonify, request
from flask_cors import CORS
from agntcy.dir_sdk.client import Client, Config
from agntcy.dir_sdk.models import search_v1, routing_v1, core_v1
from agntcy.dir.store.v1 import sync_service_pb2
from google.protobuf.json_format import MessageToDict
import os
import json
import requests

app = Flask(__name__)
CORS(app)

def get_client(node_address=None):
    """Create directory client for specified node"""
    address = node_address or os.getenv('DEFAULT_NODE_ADDRESS', 'localhost:8888')
    auth_mode = os.getenv('AUTH_MODE', 'x509')
    
    config_params = {'server_address': address}
    
    if auth_mode == 'x509':
        config_params['spiffe_socket_path'] = os.getenv('SPIFFE_SOCKET_PATH', 'unix:///run/spire/sockets/agent.sock')
        config_params['auth_mode'] = 'x509'
    elif auth_mode == 'token':
        config_params['auth_mode'] = 'token'
        config_params['token'] = os.getenv('AUTH_TOKEN', '')
    elif auth_mode == 'insecure':
        config_params['auth_mode'] = 'insecure'
    
    config = Config(**config_params)
    return Client(config)

@app.route('/api/nodes', methods=['GET'])
def get_nodes():
    """Get federation nodes from environment"""
    nodes_str = os.getenv('FEDERATION_NODES', '')
    nodes = []
    
    if nodes_str:
        for i, node_def in enumerate(nodes_str.split(','), 1):
            parts = node_def.strip().split(':')
            if len(parts) >= 2:
                name = parts[0]
                address = ':'.join(parts[1:])  # Handle port in address
                nodes.append({
                    'id': f'node{i}',
                    'address': address,
                    'name': name
                })
    
    # Fallback if no nodes configured
    if not nodes:
        nodes = [{'id': 'default', 'address': os.getenv('DEFAULT_NODE_ADDRESS', 'localhost:8888'), 'name': 'Default Node'}]
    
    return jsonify(nodes)

@app.route('/api/search', methods=['POST'])
def search():
    """Local search on specific node"""
    data = request.json
    node = data.get('node')
    query_type = data.get('type', 'name')
    query_value = data.get('value', '')
    limit = data.get('limit', 50)
    
    client = get_client(node)
    
    queries = []
    if query_value:
        if query_type == 'name':
            qtype = search_v1.RECORD_QUERY_TYPE_NAME
        elif query_type == 'skill':
            qtype = search_v1.RECORD_QUERY_TYPE_SKILL_NAME
        elif query_type == 'domain':
            qtype = search_v1.RECORD_QUERY_TYPE_DOMAIN_NAME
        else:
            qtype = search_v1.RECORD_QUERY_TYPE_NAME
        
        queries.append(search_v1.RecordQuery(type=qtype, value=query_value))
    
    req = search_v1.SearchRecordsRequest(queries=queries, limit=limit)
    
    # Get CIDs first
    cid_req = search_v1.SearchCIDsRequest(queries=queries, limit=limit)
    cid_results = list(client.search_cids(cid_req))
    cids = [r.record_cid for r in cid_results]
    
    # Get full records
    results = list(client.search_records(req))
    
    agents = []
    for i, r in enumerate(results):
        data = MessageToDict(r.record.data)
        agents.append({
            'cid': cids[i] if i < len(cids) else 'unknown',
            'name': data.get('name', 'Unknown'),
            'description': data.get('description', ''),
            'skills': [s.get('name') for s in data.get('skills', [])],
            'domains': data.get('domains', []),
            'locators': data.get('locators', [])
        })
    
    return jsonify({'results': agents, 'count': len(agents)})

@app.route('/api/routing-search', methods=['POST'])
def routing_search():
    """Federation-wide P2P search"""
    data = request.json
    node = data.get('node')
    query_type = data.get('type', 'skill')
    query_value = data.get('value', '')
    
    client = get_client(node)
    
    # For "show all", we can't use routing search (requires query)
    # Instead, show locally published records that are available for federation
    if not query_value or query_value == '*':
        from agntcy.dir.routing.v1 import routing_service_pb2
        list_req = routing_service_pb2.ListRequest()
        list_results = list(client.routing_client.List(list_req))
        
        # Get CIDs from list
        cids = [r.record_ref.cid for r in list_results]
        
        # Pull records for each CID
        from agntcy.dir_sdk.models import core_v1
        agents = []
        for cid in cids[:50]:  # Limit to 50
            try:
                refs = [core_v1.RecordRef(cid=cid)]
                records = client.pull(refs)
                if records:
                    data = MessageToDict(records[0].data)
                    agents.append({
                        'cid': cid,
                        'name': data.get('name', 'Unknown'),
                        'description': data.get('description', ''),
                        'skills': [s.get('name') for s in data.get('skills', [])],
                        'domains': data.get('domains', []),
                        'locators': data.get('locators', []),
                        'source_node': 'local-routing-table'
                    })
            except:
                pass
        
        return jsonify({
            'results': agents, 
            'count': len(agents),
            'note': 'Showing locally published records. These are in the routing table but may not be discoverable via P2P search.'
        })
    
    # Do P2P federation search
    if query_type == 'skill':
        qtype = routing_v1.RECORD_QUERY_TYPE_SKILL
    elif query_type == 'domain':
        qtype = routing_v1.RECORD_QUERY_TYPE_DOMAIN
    else:
        qtype = routing_v1.RECORD_QUERY_TYPE_SKILL
    
    req = routing_v1.SearchRequest(
        queries=[routing_v1.RecordQuery(type=qtype, value=query_value)]
    )
    
    results = list(client.routing_client.Search(req))
    
    agents = []
    for r in results:
        # Get CID and peer info
        cid = r.record_ref.cid
        source = r.peer.addrs[0] if r.peer.addrs else 'unknown'
        
        # Try to pull the record (may fail if on remote node)
        try:
            from agntcy.dir_sdk.models import core_v1
            refs = [core_v1.RecordRef(cid=cid)]
            records = client.pull(refs)
            if records:
                data = MessageToDict(records[0].data)
                agents.append({
                    'cid': cid,
                    'name': data.get('name', 'Unknown'),
                    'description': data.get('description', ''),
                    'skills': [s.get('name') for s in data.get('skills', [])],
                    'domains': data.get('domains', []),
                    'locators': data.get('locators', []),
                    'source_node': source
                })
        except:
            # Record is on remote node, return basic info
            agents.append({
                'cid': cid,
                'name': f'Agent on {source}',
                'description': 'Use sync to pull this record from remote node',
                'skills': [],
                'domains': [],
                'locators': [],
                'source_node': source
            })
    
    return jsonify({'results': agents, 'count': len(agents)})

@app.route('/api/pull', methods=['POST'])
def pull():
    """Pull full record by CID"""
    data = request.json
    node = data.get('node')
    cid = data.get('cid')
    
    client = get_client(node)
    
    from agntcy.dir_sdk.models import core_v1
    refs = [core_v1.RecordRef(cid=cid)]
    records = client.pull(refs)
    
    if records:
        record_data = MessageToDict(records[0].data)
        return jsonify(record_data)
    
    return jsonify({'error': 'Record not found'}), 404

@app.route('/api/push', methods=['POST'])
def push():
    """Push new record"""
    data = request.json
    node = data.get('node')
    record_data = data.get('record')
    
    client = get_client(node)
    record = core_v1.Record(data=record_data)
    refs = client.push([record])
    
    return jsonify({'cid': refs[0].cid, 'success': True})

@app.route('/api/publish', methods=['POST'])
def publish():
    """Publish record to federation"""
    data = request.json
    node = data.get('node')
    cid = data.get('cid')
    
    client = get_client(node)
    
    ref = core_v1.RecordRef(cid=cid)
    req = routing_v1.PublishRequest(record_refs=routing_v1.RecordRefs(refs=[ref]))
    client.publish(req)
    
    return jsonify({'success': True})

@app.route('/api/unpublish', methods=['POST'])
def unpublish():
    """Unpublish record from federation"""
    data = request.json
    node = data.get('node')
    cid = data.get('cid')
    
    client = get_client(node)
    
    ref = core_v1.RecordRef(cid=cid)
    req = routing_v1.UnpublishRequest(record_refs=routing_v1.RecordRefs(refs=[ref]))
    client.unpublish(req)
    
    return jsonify({'success': True})

@app.route('/api/sync', methods=['POST'])
def sync():
    """Create sync from remote node"""
    data = request.json
    local_node = data.get('local_node')
    remote_node = data.get('remote_node')
    cids = data.get('cids', [])
    
    client = get_client(local_node)
    
    req = sync_service_pb2.CreateSyncRequest(
        remote_directory_url=remote_node,
        cids=cids
    )
    resp = client.create_sync(req)
    
    return jsonify({'sync_id': resp.sync_id, 'success': True})

@app.route('/api/sync-status', methods=['POST'])
def sync_status():
    """Get sync status"""
    data = request.json
    node = data.get('node')
    sync_id = data.get('sync_id')
    
    client = get_client(node)
    
    req = sync_service_pb2.GetSyncStatusRequest(sync_id=sync_id)
    resp = client.get_sync_status(req)
    
    return jsonify({
        'sync_id': resp.sync_id,
        'status': resp.status,
        'total': resp.total_records,
        'synced': resp.synced_records
    })

@app.route('/api/delete', methods=['POST'])
def delete():
    """Delete record"""
    data = request.json
    node = data.get('node')
    cid = data.get('cid')
    
    client = get_client(node)
    client.delete_record(cid)
    
    return jsonify({'success': True})

@app.route('/api/skills', methods=['GET'])
def get_skills():
    """Proxy OASF skills catalog"""
    try:
        res = requests.get('https://schema.oasf.outshift.com/api/skills', timeout=10)
        return jsonify(res.json())
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/domains', methods=['GET'])
def get_domains():
    """Proxy OASF domains catalog"""
    try:
        res = requests.get('https://schema.oasf.outshift.com/api/domains', timeout=10)
        return jsonify(res.json())
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
