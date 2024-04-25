import numpy as np
num_router_l0 = int(input("Number of L0 switches : "))
num_ports = int(input("Number of switch ports : "))
num_pods = (num_router_l0 // (num_ports // 2))

num_nodes = num_router_l0 * (num_ports // 2)
node_l0_router = {i: (i//(num_ports // 2)) for i in range(num_nodes)}
node_pod = {i: (i//(num_ports * num_ports// (2*2) )) for i in range(num_nodes)}

node_l1_router = {i : (node_pod[i] * (num_ports // 2) + (i % (num_ports // 2))) for i in range(num_nodes)}

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
		#print(symbol_b)
		#print(paulls_matrix[i][column_to_search])
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
	debug = 1
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
			flows_in_different_pod.append((src, dest))
	print(same_flows_in_pods[2])		
	

	for key, values in same_flows_in_pods.items():
		print(values)
		paulls_matrix = np.empty(shape=((num_ports // 2),(num_ports // 2)), dtype='object')
		paulls_matrix.fill("%")
		rows_utilization_matrix = np.empty(shape=((num_ports // 2), (num_ports // 2)))
		column_utilization_matrix = np.empty(shape=((num_ports // 2), (num_ports // 2)))
		rows_utilization_matrix.fill(0)
		column_utilization_matrix.fill(0)
		num_unblocked = 0
		num_blocked = 0
		for (src, dest, src_rtr, dest_rtr) in values:
			blocked = 1
			for num, (i, j) in enumerate(zip(rows_utilization_matrix[src_rtr], column_utilization_matrix[dest_rtr])):
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
				grid_indices.append((grid_position, symbol_b))

				while to_search != 0:
					if count == 0:
						grid_position, to_search = search_column(paulls_matrix, symbol_a, grid_position)
						grid_indices.append((grid_position, symbol_a))
						count += 1
					elif count == 1:
						grid_position, to_search = search_row(paulls_matrix, symbol_b, grid_position)
						grid_indices.append((grid_position, symbol_b))
						count -= 1 
				if debug:
					print("one complete")		
				print(grid_indices)
				num_blocked += 1
				debug = 0
		for i in rows_utilization_matrix:
			print(np.count_nonzero(i=='%'))				
		print(paulls_matrix)
		print(rows_utilization_matrix)
		print(column_utilization_matrix)
		print(num_blocked)
		print(num_unblocked)
		break
"""

with open("jperm_0.txt", "r") as fp:
	lines = fp.readlines()
get_individual_perm_routing(lines)
'''
find_l1 = []
same_l1_flow = 0
for line in lines:
	src = int(line.split(" ")[0].strip())
	dest = int(line.split(" ")[-1].strip())
	src_l1 = node_l1_router[src]
	dest_l1 = node_l1_router[dest]
	if src_l1 != dest_l1:
		find_l1.append((src, dest, src_l1, dest_l1))
	else:
		same_l1_flow += 1


paulls_matrix = np.empty(shape=(num_router_l0,num_router_l0), dtype='object')
paulls_matrix.fill("%")
rows_utilization_matrix = np.empty(shape=(num_router_l0, num_ports))
column_utilization_matrix = np.empty(shape=(num_router_l0, num_ports))
rows_utilization_matrix.fill(0)
column_utilization_matrix.fill(0)

num_unblocked = 0
num_blocked = 0
for (src, dest, src_l1, dest_l1) in find_l1:
	blocked = 1
	for num, (i, j) in enumerate(zip(rows_utilization_matrix[src_l1], column_utilization_matrix[dest_l1])):
		if i == 0 and j == 0:
			rows_utilization_matrix[src_l1][num] = 1
			column_utilization_matrix[dest_l1][num] = 1
			paulls_matrix[src_l1][dest_l1] = paulls_matrix[src_l1][dest_l1] + "_" + str(num)
			blocked = 0
			num_unblocked += 1
			print("{} {} {}".format(src_l1, dest_l1, num))
			break
	if blocked == 1:
		print("{} {} {}".format(src_l1, dest_l1, "blocked"))
		num_blocked += 1
		

print(paulls_matrix)
print(rows_utilization_matrix)
print(column_utilization_matrix)
print(num_blocked)
print(num_unblocked)
print(same_l1_flow)
print("Check Paulls Matrix for repetation of symbol, if there is a repetation of symbol that means a link is shared")

print("First check rowise in paul matrix")
for i in range(num_router_l0):
	used_symbol = []
	for symbol in paulls_matrix[i]:
		if "_" in symbol:
			symbols_present = symbol.strip().split("_")
			for s in symbols_present:
				if s in used_symbol:
					print("Row {} has repeated symbol {}".format(i, s))
				else:
					used_symbol.append(s)
	print("Row {} has symbols {}".format(i, used_symbol))

print("Second check columnise in paul matrix")
for i in range(num_router_l0):
	used_symbol = []
	for symbol in paulls_matrix[:,i]:
		if "_" in symbol:
			symbols_present = symbol.strip().split("_")
			for s in symbols_present:
				if s in used_symbol:
					print("Column {} has repeated symbol {}".format(i, s))
				else:
					used_symbol.append(s)
	print("Column {} has symbols {}".format(i, used_symbol))
'''		
			
