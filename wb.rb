#!/usr/bin/env ruby
require 'webrick'

server = WEBrick::HTTPServer.new :Port => 8000
cgi_dir = File.expand_path("#{__dir__}/cgi-bin")
server.mount("/cgi-bin", WEBrick::HTTPServlet::FileHandler, cgi_dir)

# server.mount "/", WEBrick::HTTPServlet::FileHandler ,"#{__dir__}" # './'
trap('INT') { server.stop }
server.start
