import sys
import numpy as np
import collections
#num_router_l0 = int(input("Number of L0 switches : "))
#num_ports = int(input("Number of switch ports : "))
num_router_l0 = 64
num_ports = 32
num_pods = (num_router_l0 // (num_ports // 2))

num_nodes = num_router_l0 * (num_ports // 2)
node_l0_router = {i: (i//(num_ports // 2)) for i in range(num_nodes)}
node_pod = {i: (i//(num_ports * num_ports// (2*2) )) for i in range(num_nodes)}

node_l1_router = {i : (node_pod[i] * (num_ports // 2) + (i % (num_ports // 2))) for i in range(num_nodes)}

flow_l1_router = []
l1_router_load = [0] * num_router_l0

def all_links():
	links = {}
	for i in range(num_router_l0):
		for j in range(num_router_l0 // 2):
			links["L1_{} L2_{}".format(i, j)] = 0
	for i in range(num_router_l0 // 2):
		for j in range(num_router_l0):
			links["L2_{} L1_{}".format(i, j)] = 0
	
	for i in range(num_pods):
		start = i * (num_ports // 2)
		end = (i + 1) * (num_ports // 2) - 1
		for i in range(start, end + 1):
			for j in range(start, end + 1):
				links["L0_{} L1_{}".format(i, j)] = 0
				links["L1_{} L0_{}".format(i, j)] = 0
	return links

def search_column(paulls_matrix, symbol_a, grid_position):
	row, column_to_search = grid_position
	found = 0
	new_grid_position = ()
	for i in range(len(paulls_matrix)):
		if '_' in paulls_matrix[i][column_to_search]:
			allnumbers = paulls_matrix[i][column_to_search].split('_')
			if symbol_a in allnumbers:
				new_grid_position = (i, column_to_search)
				found = 1
				break
	if found == 1:
		return new_grid_position, 1
	else:
		return new_grid_position, 0

def search_row(paulls_matrix, symbol_b, grid_position):
	row_to_search, column = grid_position
	found = 0
	new_grid_position = ()
	for i in range(len(paulls_matrix[row_to_search])):
		if '_' in paulls_matrix[row_to_search][i]:
			allnumbers = paulls_matrix[row_to_search][i].split('_')
			if symbol_b in allnumbers:
				new_grid_position = (row_to_search, i)
				found = 1
				break
	if found == 1:
		return new_grid_position, 1
	else:
		return new_grid_position, 0

def get_individual_perm_routing(lines):
	links = all_links()
	debug = 0
	max_flow = 0
	flows_in_same_pod = []
	flows_in_different_pod = []
	same_flows_in_pods = {i : [] for i in range(num_pods)}
	for line in lines:
		src = int(line.split(" ")[0].strip())
		dest = int(line.split(" ")[-1].strip())
		src_pod = node_pod[src]
		dest_pod = node_pod[dest]
		if node_pod[src] == node_pod[dest]:
			flows_in_same_pod.append((src, dest))
			same_flows_in_pods[node_pod[src]].append((src, dest, node_l0_router[src], node_l0_router[dest]))
		else:
			flows_in_different_pod.append((src, dest, node_l0_router[src], node_l0_router[dest], src_pod, dest_pod))
	

	for key, values in same_flows_in_pods.items():
		paulls_matrix = np.empty(shape=((num_ports // 2),(num_ports // 2)), dtype='object')
		paulls_matrix.fill("%")
		rows_utilization_matrix = np.empty(shape=((num_ports // 2), (num_ports // 2)))
		column_utilization_matrix = np.empty(shape=((num_ports // 2), (num_ports // 2)))
		rows_utilization_matrix.fill(0)
		column_utilization_matrix.fill(0)
		num_unblocked = 0
		num_blocked = 0
		for (src, dest, phy_src_rtr, phy_dest_rtr) in values:
			blocked = 1
			src_rtr = phy_src_rtr - (key * (num_ports // 2))
			dest_rtr = phy_dest_rtr - (key * (num_ports // 2))
			for num, (i, j) in enumerate(zip(rows_utilization_matrix[src_rtr], column_utilization_matrix[dest_rtr])):
				if i == 0 and j == 0:
					rows_utilization_matrix[src_rtr][num] = 1
					column_utilization_matrix[dest_rtr][num] = 1
					paulls_matrix[src_rtr][dest_rtr] = paulls_matrix[src_rtr][dest_rtr] + "_" + str(num)
					if dest_rtr == 9:
						print(np.transpose(paulls_matrix)[dest_rtr])
						print(column_utilization_matrix[dest_rtr])
					blocked = 0
					num_unblocked += 1
					break
			if blocked == 1:
				symbol_a = -1
				symbol_b = -1
				for i in range(len(rows_utilization_matrix[src_rtr])):
					if rows_utilization_matrix[src_rtr][i] == 0:
						symbol_a = str(i)
						break
				for i in range(len(column_utilization_matrix[dest_rtr])):
					if column_utilization_matrix[dest_rtr][i] == 0:
						symbol_b = str(i)
						break
				to_search = 1
				count = 0
				grid_indices = []
				start_grid = None
				for i in range(len(paulls_matrix[src_rtr])):
					if '_' in paulls_matrix[src_rtr][i]:
						allnumbers = paulls_matrix[src_rtr][i].split('_')
						if symbol_b in allnumbers:
							start_grid = (src_rtr, i)
							break
				grid_position = start_grid
				grid_indices.append((grid_position, symbol_b, symbol_a))

				while to_search != 0:
					if count == 0:
						grid_position, to_search = search_column(paulls_matrix, symbol_a, grid_position)
						if to_search:
							grid_indices.append((grid_position, symbol_a, symbol_b))
							count += 1
					elif count == 1:
						grid_position, to_search = search_row(paulls_matrix, symbol_b, grid_position)
						if to_search:
							grid_indices.append((grid_position, symbol_b, symbol_a))
							count -= 1 
				num_blocked += 1
				debug = 0
				
				for (i, j), old_symbol, new_symbol in grid_indices:
					all_symbols = paulls_matrix[i][j].split('_')
					all_symbols.remove(old_symbol)
					all_symbols.append(new_symbol)
					new_string = '_'.join(all_symbols)
					paulls_matrix[i][j] = new_string
				paulls_matrix[src_rtr][dest_rtr] = paulls_matrix[src_rtr][dest_rtr] + "_" + symbol_b
				
				rows_utilization_matrix.fill(0)
				column_utilization_matrix.fill(0)
				
				for i in paulls_matrix:
					allnums = []
					for j in paulls_matrix[i]:
						if '_' in paulls_matrix[i][j]:
							allnums.extend(paulls_matrix[i][j].split('_'))


		upward_links_used = np.zeros(shape=(num_ports // 2, num_ports // 2))
		downward_links_used = np.zeros(shape=(num_ports // 2, num_ports // 2))
		print(paulls_matrix)
		print('....')
		print(np.transpose(paulls_matrix))
		for (src, dest, phy_src_rtr, phy_dest_rtr) in values:
				src_rtr = phy_src_rtr - (key * (num_ports // 2))
				dest_rtr = phy_dest_rtr - (key * (num_ports // 2))
				if '_' in paulls_matrix[src_rtr][dest_rtr]:
					list_of_router = paulls_matrix[src_rtr][dest_rtr].split('_')
					chosen_l1 = list_of_router.pop()
					if phy_dest_rtr == 9:
						print(chosen_l1)
						print(list_of_router)
						print(paulls_matrix[src_rtr][dest_rtr])	
					if chosen_l1 != '%':
						chosen_l1 = int(chosen_l1) + (key * (num_ports // 2))
						upward_links_used[src_rtr][chosen_l1 - (key * (num_ports // 2))] += 1
						downward_links_used[dest_rtr][chosen_l1 - (key * (num_ports // 2))] += 1
						flow_l1_router.append((src, dest, phy_src_rtr, phy_dest_rtr, chosen_l1))
						paulls_matrix[src_rtr][dest_rtr] = '_'.join(list_of_router)
				
		#print(f'Pauls Matrix in pod {key} is {paulls_matrix} transposed {paulls_matrix.transpose()}')
		#print(f'Row Ulilization Matrix in pod {key} is {rows_utilization_matrix}')
		#print(f'Column Utilization Matrix in pod {key} is {column_utilization_matrix}')
		#print(f'Number of blocked flows in pod {key} is {num_blocked}')
		#print(f'Number of unblocked flows in pod {key} is {num_unblocked}')
		#print(f'The flows are {flow_l1_router}')
		print('......')
		print(upward_links_used)
		print(downward_links_used)
		break
	#print(links)
	#print(flow_l1_router)
	#for key, value in links.items():
	#	if value == 2:
	#		print(key)
'''
	paulls_matrix = np.empty(shape=((num_router_l0),(num_router_l0)), dtype='object')
	paulls_matrix.fill("%")
	rows_utilization_matrix = np.empty(shape=((num_router_l0), (num_router_l0 // 2)))
	column_utilization_matrix = np.empty(shape=((num_router_l0), (num_router_l0 // 2)))
	rows_utilization_matrix.fill(0)
	column_utilization_matrix.fill(0)
	num_unblocked = 0
	num_blocked = 0
	pre_flow = []
	for src, dest, phy_src_rtr, phy_dest_rtr, src_pod, dest_pod in flows_in_different_pod:
		l1_router_load[chosen_l1]
		src_strt_rtr = (src_pod * (num_ports // 2))
		src_end_rtr = ((src_pod + 1) * (num_ports // 2)) - 1
		dest_strt_rtr = (dest_pod * (num_ports // 2))
		dest_end_rtr = ((dest_pod + 1) * (num_ports // 2)) - 1
		min_src_router = sys.maxsize
		min_dest_router = sys.maxsize
		src_l1 = None
		dest_l1 = None
		for i in range (src_strt_rtr, src_end_rtr + 1):
			if links["L0_{} L1_{}".format(phy_src_rtr, i)] == 0:
				src_l1 = i
				break
		for i in range (dest_strt_rtr, dest_end_rtr + 1):
			if links["L1_{} L0_{}".format(i, phy_dest_rtr)] == 0:
				dest_l1 = i
				break
		l1_router_load[src_l1] += 1
		l1_router_load[dest_l1] += 1	
		pre_flow.append((src, dest, phy_src_rtr, phy_dest_rtr, src_l1, dest_l1))
		blocked = 1
		src_rtr = src_l1
		dest_rtr = dest_l1
		print(src_rtr, dest_rtr)
		for num, (i, j) in enumerate(zip(rows_utilization_matrix[src_rtr], column_utilization_matrix[dest_rtr])):
			print(f'num is {num} i in {i} and j is {j}')
			if i == 0 and j == 0:
					rows_utilization_matrix[src_rtr][num] = 1
					column_utilization_matrix[dest_rtr][num] = 1
					paulls_matrix[src_rtr][dest_rtr] = paulls_matrix[src_rtr][dest_rtr] + "_" + str(num)
					blocked = 0
					num_unblocked += 1
					#print("{} {} {}".format(src_rtr, dest_rtr, num))
					break
		if blocked == 1:
				if debug:
					print(paulls_matrix)
					print("{} {} {}".format(src_rtr, dest_rtr, "blocked"))
				symbol_a = -1
				symbol_b = -1
				if debug:
					print(rows_utilization_matrix[src_rtr])
				for i in range(len(rows_utilization_matrix[src_rtr])):
					if rows_utilization_matrix[src_rtr][i] == 0:
						symbol_a = str(i)
						break
				if debug:
					print(column_utilization_matrix[dest_rtr])
				for i in range(len(column_utilization_matrix[dest_rtr])):
					if column_utilization_matrix[dest_rtr][i] == 0:
						symbol_b = str(i)
						break
				if debug:
					print("Symbol a {} /// Symbol b {}".format(symbol_a, symbol_b))
				to_search = 1
				count = 0
				grid_indices = []
				if debug:
					print(paulls_matrix[src_rtr])
				start_grid = None
				print(f'Pauls {paulls_matrix[src_rtr]}')
				for i in range(len(paulls_matrix[src_rtr])):
					if '_' in paulls_matrix[src_rtr][i]:
						allnumbers = paulls_matrix[src_rtr][i].split('_')
						if debug:
							print(allnumbers)
						if symbol_b in allnumbers:
							if debug:
								print(symbol_b)
								print(paulls_matrix[src_rtr][i])
							start_grid = (src_rtr, i)
							if debug:
								print("Found start {}".format(start_grid)) 
							break
				grid_position = start_grid
				print(f'grid {grid_position}')
				grid_indices.append((grid_position, symbol_b, symbol_a))

				while to_search != 0:
					if count == 0:
						grid_position, to_search = search_column(paulls_matrix, symbol_a, grid_position)
						if to_search:
							grid_indices.append((grid_position, symbol_a, symbol_b))
							count += 1
					elif count == 1:
						grid_position, to_search = search_row(paulls_matrix, symbol_b, grid_position)
						if to_search:
							grid_indices.append((grid_position, symbol_b, symbol_a))
							count -= 1 
				if debug:
					print("one complete")		
				print(grid_indices)
				num_blocked += 1
				debug = 0
				for (i, j), old_symbol, new_symbol in grid_indices:
					print(f'Row {i} Column {j} Symbol {old_symbol}')
					all_symbols = paulls_matrix[i][j].split('_')
					all_symbols.remove(old_symbol)
					all_symbols.append(new_symbol)
					new_string = '_'.join(all_symbols)
					paulls_matrix[i][j] = new_string
				rows_utilization_matrix[src_rtr][int(symbol_a)] = 1
				column_utilization_matrix[dest_rtr][int(symbol_b)] = 1
				paulls_matrix[src_rtr][dest_rtr] = paulls_matrix[src_rtr][dest_rtr] + "_" + symbol_b
				
	final_flow = []	
	for (src, dest, phy_src_rtr, phy_dest_rtr, src_l1, dest_l1) in pre_flow:
				src_rtr = src_l1
				dest_rtr = dest_l1
				if '_' in paulls_matrix[src_rtr][dest_rtr]:
					list_of_router = paulls_matrix[src_rtr][dest_rtr].split('_')
					chosen_l1 = list_of_router.pop()
					if chosen_l1 != '%':
						paulls_matrix[src_rtr][dest_rtr] = '_'.join(list_of_router)
						chosen_l1 = int(chosen_l1)
						#l1_router_load[chosen_l1] += 1
						#links["L0_{} L1_{}".format(i, j)] = 0
					final_flow.append((src, dest, phy_src_rtr, phy_dest_rtr, src_l1, dest_l1, chosen_l1))
	flow_l1_router.extend(final_flow)
		
	print(flow_l1_router)
	for i in flow_l1_router:
		#if len(i) == 5:
			#links["L0_{} L1_{}".format(i[2], i[4])] += 1
			#links["L1_{} L0_{}".format(i[4], i[3])] += 1
		if len(i) == 7:	
			links["L0_{} L1_{}".format(i[2], i[4])] += 1
			links["L1_{} L0_{}".format(i[5], i[3])] += 1
			links["L1_{} L2_{}".format(i[4], i[6])] += 1
			links["L2_{} L1_{}".format(i[6], i[5])] += 1
	print(len(i))
	print(links)
	print(flow_l1_router)
	for key, value in links.items():
		if value == 2:
			print(key)
'''
with open("jperm_0.txt", "r") as fp:
	lines = fp.readlines()
get_individual_perm_routing(lines)
