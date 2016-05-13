import re
import os

dir = 'C:/Users/jan.murin/Desktop/Scripting/cdp/vw'

def read_files(vstup):
	vypis = []
	for filename in os.listdir(vstup):
		#print filename		#vypise len mena suborov v adresari "cdp_dir"
		path = os.path.join(vstup, filename)	#definicia adresaru
		#print path		#vypise celu cestu s menom suborov v adresari "path"
		input = open(path).readlines()		#precitanie subora v adresari "path"
	
		vypis.append(input)
		
	return vypis

test = ['riadok1#','Device ID        Local Intrfce     Holdtme    Capability  Platform  Port ID','riadok3#','riadok4#','poslednyriadok#riadok5']

#zisti aky typ subora to je - config, cdp alebo int_status (zvysok je unknown)
def file_type(vstup):
	dev_type = {}
	dev_type['device'] = vstup[-1].split('#')[0]
	
	for line in vstup:
		if re.match('hostname .*', line):
			dev_type['device'] = re.search('hostname (\S+)', line).group(1)
			dev_type['type'] = 'config'
			break
			
		elif re.search('Device ID        Local Intrfce .*', line):
			dev_type['type'] = 'cdp'
			break
			
		elif re.search('Port      Name .*', line):
			dev_type['type'] = 'int_status'
			break
			
		else:
			dev_type['type'] = 'unknown'

	return dev_type

#len zoberie pole nacitanych suborov a prebehne na nich funkciu file_type	
def file_evaluation(vstup):
	output = []
	
	for file in vstup:
		output.append(file_type(file))
		
	return output
	

		

#funkcia zoberie obsah suborov a ich zistene typy (z funkcie file_evaluation)
#vytovri dict kde budu key = hostname a v nich budu dict, ktore mozu obsahovat key = config,
#cdp alebo int_status. Podla toho, ktore vstupy su k dispozicii
def file_output(subory, hodnotenie_suborov):
	output = {}
	
	for i in range(0,len(subory)):
		dev_out = {}
		zariadenie = hodnotenie_suborov[i]['device']
		
		#najprv zoberiem vstupy a zapisem podla typu subora jeho obsah do spravneho 'key'(dict dev_out)
		
		#cdp uz rovno aj parsujem
		if hodnotenie_suborov[i]['type'] == 'cdp':
			cdp_out = cdp_parse(subory[i])
			dev_out['cdp'] = cdp_out
			
		elif hodnotenie_suborov[i]['type'] == 'config':
			dev_out['config'] = subory[i]
		
		elif hodnotenie_suborov[i]['type'] == 'int_status':
			dev_out['int_status'] = subory[i]
		
		#nasledne riesim, aby vsetky subory patriace tomu istemu zariadeniu boli v tom istom key (dict output)
		if len(output) == 0:
			output[zariadenie] = dev_out
			
		else:
			existuje = False
			for key in output:
				if key == zariadenie:
					existuje = True
					
				else:
					continue
			
			if existuje:
				output[zariadenie].update(dev_out)
				
			else:
				output[zariadenie] = dev_out

			
	return output
	


#parsuje config rozhrani - momentalne vytiahne len potrebne riadky 'switchport trunk allowed vlan ...'
def config_parse(hladana_cast, zdrojovy_subor):
	parse_config = []

	for line in zdrojovy_subor:

		if re.match(hladana_cast, line):
			parse_config.append(line)
			
		elif len(parse_config) != 0:
		
			#zaujimaju ma len riadky s trunk konfiguraciou
			if re.match(' .*', line):
				if re.match(' switchport trunk allowed vlan .*', line):
					parse_config.append(line)

				
			#elif line == '!':
				#break
				
			else:
				break
			
	del parse_config[0]
	return parse_config

#parsuje cdp vystup kde hlada meno suseda, rozhrania	
def cdp_parse(vstup):

	for i, j in enumerate(vstup):
		
		if re.match('\s+\S+', j):
			vstup[i-1] = vstup[i-1] + vstup[i]
			del vstup[i]
			
		else:
			pass

			
	cdp_line = []	
	for i in vstup:
		cdp_info = {}
		
		if re.search('(\S+)\s+((?:Fas|Gig) \S+)\s+(\d+)\s+((?:[A-Z] )*).*(?:((?:Eth|Gig|Fas) \S+)$|(?:Port|LAN|eth).*)', i):
			#print re.search('(\S+)\s+((?:Fas|Gig) \S+)\s+(\d+)(?:\s+\S+)* *((?:(?:Eth|Gig|Fas|Port) \S+)|(?:LAN|eth0))', i).groups()
			#print re.search('(\S+)\s+((?:Fas|Gig) \S+)\s+(\d+)\s+((?:[A-Z] )*).*(?:((?:Eth|Gig|Fas) \S+)$|(?:Port|LAN|eth).*)', i).groups()
			
			#nasledna uprava vystupu, aby som to vedel spracovat spolu s configom
			cdp_info['my_int'] = re.search('(\S+)\s+((?:Fas|Gig) \S+)\s+(\d+)\s+((?:[A-Z] )*).*(?:((?:Eth|Gig|Fas) \S+)$|(?:Port|LAN|eth).*)', i).group(2)
			if cdp_info['my_int'] != None and re.search('Fas (\S+)',cdp_info['my_int']):
				cdp_info['my_int'] = 'interface FastEthernet' + re.search('(?:\S) (\S+)',cdp_info['my_int']).group(1)
				
			elif cdp_info['my_int'] != None and re.search('Gig (\S+)',cdp_info['my_int']):
				cdp_info['my_int'] = 'interface GigabitEthernet' + re.search('(?:\S) (\S+)',cdp_info['my_int']).group(1)
			
			
			cdp_info['nei_int'] = re.search('(\S+)\s+((?:Fas|Gig) \S+)\s+(\d+)\s+((?:[A-Z] )*).*(?:((?:Eth|Gig|Fas) \S+)$|(?:Port|LAN|eth).*)', i).group(5)
			if cdp_info['nei_int'] != None and re.search('Fas (\S+)',cdp_info['nei_int']):
				cdp_info['nei_int'] = 'interface FastEthernet' + re.search('(?:\S) (\S+)',cdp_info['nei_int']).group(1)
				
			elif cdp_info['nei_int'] != None and re.search('Gig (\S+)',cdp_info['nei_int']):
				cdp_info['nei_int'] = 'interface GigabitEthernet' + re.search('(?:\S) (\S+)',cdp_info['nei_int']).group(1)				
				
			cdp_info['nei'] = re.search('(\S+)\s+((?:Fas|Gig) \S+)\s+(\d+)\s+((?:[A-Z] )*).*(?:((?:Eth|Gig|Fas) \S+)$|(?:Port|LAN|eth).*)', i).group(1)
			cdp_info['nei'] = cdp_info['nei'].split('.')[0]
			cdp_line.append(cdp_info)

		
	return cdp_line

#funkcia, ktora spracuje vstupy a vyhodnoti trunky kde su cdp susedia
#ak mam cdp vstup zistim susedov
#vytiahnem konfiguraciu  rozhrania suseda (ak konfig mam) - na zaklade mena suseda a zistreneho rozhrania
#rovnako vytiahnem konfig mojho rozhrania
#konfiguracie rozhrani porovnam ci su trunky rovnako nakonfigurovane

def cdp_evaluation(vstup):
#vstupom su uz roztriedene subory podla zariadeni a typu
#vystup je dict s keys [device] a vnutri budu dict s my_int_config, nei_int a nei

	overall_output = {}

	#najprv do dict overall_output vlozim pre kazdy riadok z cdp moje rozhranie, konfig rozhr, nei a rozhr. nei.
	for device in vstup:
		device_output = []
			
		if 'cdp' in vstup[device]:
		
			for line in vstup[device]['cdp']:
				device_cdp_out = {}
			
				device_cdp_out['my_int'] = line['my_int']
				
				#riesim problem ci mam config zo zariadenia
				if 'config' in  vstup[device]: 
					device_cdp_out['my_int_config'] = config_parse(line['my_int'],vstup[device]['config'])
			
				else:
					device_cdp_out['my_int_config'] = ['NO INPUT DATA']
			
			
				device_cdp_out['nei'] = line['nei']
				device_cdp_out['nei_int'] = line['nei_int']
				
				
				#musim vyriesit ci vobec mam nejaky vstup od susedneho zariadenia
				if line['nei'] in vstup:
				
					if 'config' in  vstup[line['nei']]:
						device_cdp_out['nei_int_config'] = config_parse(line['nei_int'],vstup[line['nei']]['config'])
						
					else:
						pass
				#ak vstup nemam	
				else:
					device_cdp_out['nei_int_config'] = ['NO INPUT DATA']
			
				device_output.append(device_cdp_out)
			
		else:
			continue	
			
		
		overall_output[device] = device_output
	
	#nasledne dict overall_output idem vyhodnotit, cize porovnat konfiguraciu rozhrani
	#ak nie je rovnaka, vlozim medzi chyby
	final_output = []
	
	for device in overall_output:
		for line in overall_output[device]:
			mistakes = {}			
			
			if set(line['my_int_config']) != set(line['nei_int_config']):
				mistakes['device'] = device
				mistakes['nei'] = line['nei']
				mistakes['my_int_config'] = line['my_int_config']
				mistakes['my_int'] = line['my_int']
				mistakes['nei_int'] = line['nei_int']
				mistakes['nei_int_config'] = line['nei_int_config']
				final_output.append(mistakes)	

				
	#zmazanie duplicit vo vystupe	
	for i in final_output:		
		for j in final_output:
			if i['device'] == j['nei'] and i['my_int'] == j['nei_int']:
				final_output.remove(j)
				break
	
	copy_fo = list(final_output)
	for i in copy_fo:
		if 'NO INPUT DATA' in i['nei_int_config']: #or i['my_int_config'] == ['NO INPUT DATA']:
			final_output.remove(i)
		
		else:
			pass
	
	
	return final_output

		
			
			
#funkcia vypise len v prehladnej forme najdene nedostatky v konfiguracii trunk rozhrani
def print_mistakes(vstup):
	if len(vstup) == 0:
		print '\n'
		print '-' * 20
		print "Nenasli sa ziadne chyby"
		print '-' * 20
		print '\n'
		
	else:
		for chyba in vstup:
			print '\n'
			#print '-' * 20
			print "\nZariadenie:", chyba['device']
			print "Rozhranie:", chyba['my_int']
			print "Konfiguracia rozhrania:", chyba['my_int_config']
			print "\nSused:", chyba['nei']
			print "Rozhranie suseda:", chyba['nei_int']
			print "Konfiguracia rozhrania:", chyba['nei_int_config']
			print '\n'
			print '-' * 20
			
		print '\n\nPocet najdenych chyb:', len(vstup)
		print '\n\n'
		
		
file_eval = file_evaluation(read_files(dir))
files = read_files(dir)

print_mistakes(cdp_evaluation(file_output(files, file_eval)))
