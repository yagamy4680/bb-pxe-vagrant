#!/usr/bin/env lsc
#
require! <[fs]>
require! <[tftp-server request yargs colors]>

COLORIZED = (v) ->
	t = typeof v
	return v.yellow if t is \string
	return v.to-string! .green if t is \number
	return v.to-string! .magenta if t is \boolean and v
	return v.to-string! .red if t is \boolean and not v
	return (JSON.stringify v).blue if t is \object
	return v

PRETTIZE_KVS = (kvs, separator=", ") ->
	xs = [ "#{k.gray}:#{COLORIZED v}" for k, v of kvs ]
	return xs.join separator

HANDLE_ERR = (prefix, url, next, err) ->
	console.error "#{prefix}: #{url.red} => #{err}"
	console.dir err
	return next err

argv = global.argv = yargs
	.alias \b, \bind
	.describe \b, 'the address of tftp server to bind, by default 0.0.0.0:69'
	.default \b, '0.0.0.0:69'
	.alias \n, \next
	.describe \n, 'the URL of next http server to handle the http request'
	.default \n, 'http://127.0.0.1:7090'
	.alias \l, \lease
	.describe \l, 'the path to dns lease file served by dnsmasq'
	.default \l, '/var/lib/misc/dnsmasq.leases'
	.demandOption <[bind next lease]>
	.strict!
	.help!
	.argv

{bind, next, lease} = argv
[address, port] = bind.split ':'
port = parseInt port
opts = {port, address}

console.log "address: #{address}"
console.log "port: #{port}"
console.log "lease: #{lease}"
console.log "next: #{next}"

srv = tftp-server.createServer 'udp4'

srv.bind opts, (err) ->
	return console.error "failed to bind port: #{JSON.stringify opts}, err: #{err}" if err?
	return console.log "successfully bind server: #{JSON.stringify opts}"

srv.register (req, res, n) ->
	{address, filename, mode} = req
	f = "/#{filename}"
	prefix = "[#{address.cyan}:#{f.yellow}]"
	url = "#{next}/#{filename}"
	console.log "#{prefix}: receives #{mode.blue} request"
	ip = req.address
	buffer = fs.readFileSync lease
	return HANDLE_ERR prefix, url, n, new Error "failed to load dhcp leases" unless buffer?
	text = buffer.toString!
	xs = text.split '\n'
	xs = [ x for x in xs when x.length > 0 ]
	xs = [ (x.split ' ') for x in xs ]
	xs = [ x for x in xs when x.length >= 3 and x[2] is ip ]
	[time, mac] = xs[0]
	console.log "#{prefix}: found its mac address #{mac.magenta}"
	qs = {mac, ip}
	encoding = null
	console.log "#{prefix}: forwarding request to #{url.green}"
	(err, rsp, body) <- request.get {url, qs, encoding}
	return HANDLE_ERR prefix, url, n, new Error "failed to forward: #{err}" if err?
	return HANDLE_ERR prefix, url, n, new Error "failed to forward: non-200-code: #{rsp.statusCode}" unless rsp.statusCode is 200
	console.log "#{prefix}: got #{body.length} bytes successfully."
	# console.log "#{prefix}: headers => #{PRETTIZE_KVS rsp.headers}"
	return res new Buffer body

console.log "trying to bind #{bind} ..."
