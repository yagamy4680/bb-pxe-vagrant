#!/usr/bin/env lsc
#
require! <[tftp-server request fs]>

opts = port: 69, address: '0.0.0.0'
srv = tftp-server.createServer 'udp4'
srv.bind opts, (err) ->
	return console.error "failed to bind port: #{JSON.stringify opts}, err: #{err}" if err?
	return console.log "successfully bind server: #{JSON.stringify opts}"
srv.register (req, res, next) ->
	console.log "incoming #{JSON.stringify req}"
	ip = req.address
	buffer = fs.readFileSync '/var/lib/misc/dnsmasq.leases'
	return next new Error "failed to load dhcp leases" unless buffer?
	text = buffer.toString!
	xs = text.split '\n'
	xs = [ x for x in xs when x.length > 0 ]
	xs = [ (x.split ' ') for x in xs ]
	xs = [ x for x in xs when x.length >= 3 and x[2] is ip ]
	[time, mac] = xs[0]
	qs = {mac, ip}
	url = "http://10.42.0.171:7090/#{req.filename}"
	(err, rsp, body) <- request.get {url, qs}
	return next new Error "failed to forward: #{err}" if err?
	return next new Error "failed to forward: non-200-code: #{rsp.statusCode}" unless rsp.statusCode is 200
	return res new Buffer body
	return next new Error "nothing is supported"
console.log "..."
