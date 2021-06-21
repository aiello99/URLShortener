#!/usr/bin/python
from redis import Redis, RedisError
from redis.sentinel import Sentinel
from cassandra.cluster import Cluster
from fastapi import FastAPI, BackgroundTasks
from fastapi.responses import PlainTextResponse, RedirectResponse
from typing import Optional
import time
import os
import socket
import subprocess 

# get IP address of all cassandra swarm nodes dns lookup
def getCassandraNodeIPs():
	process = subprocess.Popen(["nslookup", "tasks.cassandraswarm"], stdout=subprocess.PIPE, encoding='utf8')
	output = process.communicate()[0].split('\n')

	cass_nodes = []
	for data in output:
		if 'Address' in data:
			cass_nodes.append(data.replace('Address: ',''))
	return cass_nodes[1:]

# get IP address of all redis sentinel nodes via dns lookup
def getRedisNodeIPs():
	process = subprocess.Popen(["nslookup", "tasks.redis-sentinel"], stdout=subprocess.PIPE, encoding='utf8')
	output = process.communicate()[0].split('\n')

	redis_sentinels = []
	for data in output:
		if 'Address' in data:
			redis_sentinels.append(data.replace('Address: ',''))
	return redis_sentinels[1:]

#log messages to docker 
def log(message): 
	print("LOGGER: " + message, flush=True)

#get resources from cache then cassandra 
def get(shortResource): 
	longResource = slave.get(shortResource)
	if longResource:
		longResource = longResource.decode()
		if longResource == "NONE":
			return None
		else:
			return longResource
	else:
		statement = "SELECT * FROM shortlongtable WHERE short=%s"
		try:
			row = session.execute(statement, [shortResource]).one()
		except:
			log("cassandra failed")
			return None

		if row is None:
			try:
				master.set(shortResource, "NONE", ex=10)
			except:
				log("redis failed")
			return None

		_, longResource = row
		try:
			master.set(shortResource, longResource, ex=10)
		except:
			log("redis failed")
		return longResource

#saves resource to redis and cassandra 
def save(shortResource, longResource):
	if slave.get(shortResource) == longResource:
		return

	try:
		master.set(shortResource, longResource, ex=10)
	except:
		log("redis failed")

	try:
		statement = "INSERT INTO shortlongtable (short, long) VALUES (%s, %s);"
		session.execute(statement, [shortResource, longResource])
	except:
		log("cassandra failed")
		return "FAILED"


app = FastAPI()

#end point for get requests
@app.get('/{shortResource}')
def shortToLong(shortResource):
	log(f"received GET request for {shortResource}")
	longResource = get(shortResource)
	if longResource:
		if not longResource.startswith("http://") and not longResource.startswith("https://"):
			longResource = f"https://{longResource}"
		return RedirectResponse(longResource, status_code=307)
	else:
		return PlainTextResponse(f"PAGE NOT FOUND, your short does not exist ({socket.gethostname()})", status_code=404)

#end point for put requests 
@app.put('/', response_class=PlainTextResponse)
def longToShort(background_tasks: BackgroundTasks, short: Optional[str] = None, long: Optional[str] = None, ):
	log(f"received PUT request from {short} to {long}")
	if not short or not long:
		return PlainTextResponse(f"BAD REQUEST {short} {long} ({socket.gethostname()})", status_code=400) 
	else:
		save(short, long)
		return PlainTextResponse(f"saving {short}->{long} ({socket.gethostname()})", status_code=200) 

# connect to the cassandra cluster
cass_nodes = getCassandraNodeIPs()
try:
	cluster = Cluster(cass_nodes)
	session = cluster.connect('cassandraa2keyspace')
except: #when trying to connect to cassandra before its ready, quit and let docker restart you. 
	exit(1)

# connect to redis master and slaves
redis_sentinels = getRedisNodeIPs()
sentinels = Sentinel(map(lambda ip: (ip, 16379), redis_sentinels))
master = sentinels.master_for('master-node', socket_timeout=0.1)
slave = sentinels.slave_for('master-node', socket_timeout=0.1)
