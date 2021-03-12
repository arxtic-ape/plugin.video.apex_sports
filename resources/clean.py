import os
 
source = './'
for root,dirs,files in os.walk(source):
	for f_name in files:
		if f_name.endswith(('.pyc', '.pyo')):
			f_name = os.path.join(root, f_name)
			print(f_name) # Test to see that's it okay first 
			os.remove(f_name)
	# for folder in dirs:
	# 	if folder == '__pycache__':
	# 		