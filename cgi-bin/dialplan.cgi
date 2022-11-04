#!/usr/bin/env ruby
# frozen_string_literal: false

require 'cgi'
require 'json'
require 'drb'
require 'logger'
require 'timeout'
require 'nokogiri'
require 'date'
require 'json'

D = true

def find(string, type, doc)
  result = doc.xpath(string)
  case type
  when 'text'
    result[0].children[0].to_s
  when 'integer'
    result[0].children[0].to_s.to_i
  when 'date'
    parse(result[0].children[0])
  end
rescue StandardError
  'unknown'
end

def parse(txt_date_object)
  DateTime.strptime(txt_date_object.to_s.slice(0, 10), '%s')
end

config = JSON.parse(File.read("#{__dir__}/config.json"))

$servers = config['servers'].shuffle
$logger = Logger.new(config['logger'], config['logging'])

class Remote
  def rotate(data, type)
    $servers.each do |s|
      case type
      when 'cdr'
        @answer = request_insert(s, data)
      end
      break
    rescue StandardError
      nil
    end
    @answer || nil
  end

  private

  def request_insert(srv, insert_hash)
    status = Timeout.timeout(3) do
      remote_obj = DRbObject.new_with_uri(srv)
      ret = remote_obj.cdr_insert(insert_hash)
    end
  end
end

def printheader
  puts '<?xml version="1.0" encoding="UTF-8" standalone="no"?>'
  puts '<document type="freeswitch/xml">'
  puts '<section name="dialplan" description="Dynamic Routing">'
  puts '<context name="public">'
end

def check_xml
  dialplan_xml = "#{__dir__}/custom.xml"
  xml_file = File.read(dialplan_xml) if File.exist?(dialplan_xml)
  custom_xml = Nokogiri::XML(xml_file)
  if xml_file && custom_xml.errors.any?
    $logger.error "Wrong XML: #{custom_xml.error.inspect}"
  elsif xml_file
    $logger.debug "XML file: #{xml_file}"
    puts xml_file
  else
    $logger.debug 'No xml file found'
  end
end

def printfooter
  puts '</context>'
  puts '</section>'
  puts '</document>'
end

cgi = CGI.new
params = cgi.params
# puts "Content-type: text/plain\r\n\r\n"
# puts cgi.header(content_type_string = 'text/plain')
$logger.info '******params*******' if D

if D
  params.each do |parameter|
    $logger.debug parameter.to_s
  end
end

$logger.info '*****end params****' if D
if !params['cdr'].empty?
  $logger.info 'CDR ARRIVED' if D
  input_doc = params['cdr'].join.to_s
  # doc = File.open('test.xml') { |f| Nokogiri::XML(f) }
  doc = Nokogiri::XML(input_doc)
  if D
    $logger.debug '******cdr********'
    params['cdr'].each do |cdr_input|
      $logger.debug cdr_input
    end
    $logger.debug '*****end cdr*****'
  end
  input_hash = {
    'calldate': ['//created_time', 'date'],
    'clid': ['//caller_id_name', 'text'],
    'src': ['//randomdid', 'text'],
    'dst': ['//destination_number', 'text'],
    'dcontext': ['//context', 'text'],
    'channel': ['//chan_name', 'text'],
    'dstchannel': ['//bridge_channel', 'text'],
    'lastapp': ['//last_app', 'text'],
    'lastdata': ['//last_arg', 'text'],
    'duration': ['//duration', 'integer'],
    'billsec': ['//flow_billsec', 'integer'],
    'start': ['//start_epoch', 'date'],
    'answer': ['//answer_epoch', 'date'],
    'end': ['//end_epoch', 'date'],
    'disposition': ['//originate_disposition', 'text'],
    'amaflags': ['//amaflags', 'text'],
    'accountcode': ['//accountcode', 'text'],
    'userfield': ['//pincode', 'text'],
    'uniqueid': ['//call_uuid', 'text']
  }

  insert_hash = {}
  input_hash.each do |k, v|
    insert_hash[k] = find(v[0], v[1], doc)
  end

  $logger.debug insert_hash
  resp = Remote.new.rotate(insert_hash, 'cdr')
  if resp 
    headers_hash = { status: 200, type: 'text/plain' }
    puts cgi.header(headers_hash)
    pp resp
    $logger.error 'CDR INSERT DONE'
  else
    headers_hash = { status: 500, type: 'text/plain', connection: 'close' }
    puts cgi.header(headers_hash)
    $logger.error 'CDR INSERT FAILED'
  end

elsif !params['Caller-Destination-Number'].empty?
  didnumber = params['Caller-Destination-Number']
  begin
    $logger.info "NEW CALL FOUND DID: #{didnumber}"
#    headers_hash = { status: 200, type: 'text/plain' }
#    puts cgi.header(headers_hash)
    puts cgi.header(content_type_string = 'text/plain')
    printheader
    puts check_xml
  rescue StandardError => e
    p e
    $logger.error e
  end
  printfooter

else
  headers_hash = { status: 404, type: 'text/plain', connection: 'close' }
  puts cgi.header(headers_hash)
  puts 'Not found'

end
exit
=======
