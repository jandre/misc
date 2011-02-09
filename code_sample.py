import os,sys,getopt

usage_desc = """
#####
#  prints files and directory names, recursively
#
# -p path	 path to print.  default = "."  
# -o (html|text) output formatting.  default = text
# -w filename	 If no filename is provided will write to stdout.
# 
# note: this code will not follow symlinks to avoid loops.
# apologies for any "unpythonic" code as python isn't my strongest language
#
####
"""

FILE, DIRECTORY, LINK = range(3)

class HtmlTreeFormatter:
	cssClasses = {
		FILE: "file",
		DIRECTORY: "dir",
		LINK: "symlink"
	}	

	def __init__(self, printer):
		self.printer = printer
		self.printer.write("""
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN"
"http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
	<html><head>
			<style>

				.dir {  }
			
				div.dir span { font-weight: bold; cursor: pointer; }
				.file {  }
				
				.symlink { color: green; }

				.root { display: block; } 

			 	div.root span { font-weight: bold; cursor: pointer; }	
			</style>

			<script type=\"text/javascript\">

				function getChildren(item) {
					<!-- find parent div; return child -->
				}
				function showHide(item) {
					
					var children = item.parentNode.childNodes;
					for (var i = 0; i < children.length; i++) {
						m = children[i];
						if (m.nodeName == "DIV") {
							if (m.style.display == "none")
							m.style.display = "block";
							else
							m.style.display = \"none\";}						}
				}
			</script>
		</head><body>""")

	def print_item(self, item, level, type):	
		self.start_print(item,level,type)
		self.end_print()

	def get_style(self, level):
		style = "padding-left: 10px;"
		if level > 1:
			style += "display: none;"
		return style
	
	
	# TODO: should really html-escape chars in pathnames, to be safe. 		
	def start_print(self, item, level, type, filescount=0):
		
		self.printer.write("<div style=\"" + self.get_style(level) + "\" class=\"" + self.cssClasses[type] + "\">")
			
		# if a directory, wrap the name in a span with a special click handler.
		if type == DIRECTORY:
			self.printer.write("<span onclick=\"showHide(this);\">%s: (%d)</span>" % (item, filescount))
		else:
			self.printer.write(item);

	def end_print(self):
		self.printer.write("</div>");
	
	def close(self):
		self.printer.write("</body></html>")
		self.printer.close()
		 			

	

class TextTreeFormatter:
	" Prints directories in a text format."
	spacer = " "
	end_print = lambda(self): None
	
	def __init__(self, printer):
		self.printer = printer
		self.start_print = self.print_item
		self.close = self.printer.close

	
	def print_item(self, item, level, type, filescount=0):
		 if (type == DIRECTORY):
		 	item = "%s: (%d)" % (item, filescount)
		 self.printer.write ((self.spacer * level) + item + '\n')
		


def print_tree(file, formatter):
	""" Prints a file or directory recursively.
	    params:
		file - starting file or directory
		formatter - output formatter		
	 """
	print_tree_helper(file,0,formatter)
	formatter.close()

def print_tree_helper(file, level, formatter):
	
	if os.path.islink(file):
		formatter.print_item("*" + os.path.basename(file), level, LINK)
	elif os.path.isdir(file):
		files = sorted(os.listdir(file))
		# print the full directory name 		
		formatter.start_print(file, level, DIRECTORY, len(files))
		# recursively print out all files underneath.
		for child in files:
			print_tree_helper(os.path.join(file, child), level + 1, formatter)
		formatter.end_print()
	else:
		formatter.print_item(os.path.basename(file), level, FILE)

def try_get_sort(input):
	" returns sort or exits and prints usage "
	if input == "dir":
		return directories_first_sort
	elif input == "alpha":
		return alpha_sort
	else:
		print "-s value is wrong; valid values are 'dir' or 'alpha'"
		usage()
		sys.exit(2)		
		
class FileOutputter:

	def __init__(self, filename):	
		self.file = open(filename, 'w')
		self.close = self.file.close
		self.write = self.file.write

class StdoutOutputter:
	def __init__(self):
		self.close = lambda: None
		self.write = lambda(item): sys.stdout.write(item)
	
def validate_path(p):
	if not os.path.exists(p):
		print p + ": not a valid path or file."
		sys.exit(2)

def usage():
	print usage_desc
	
def try_get_format_maker(input):
	if input == "html":
		return lambda(o): HtmlTreeFormatter(o)
	elif input == "text":
		return lambda(o): TextTreeFormatter(o) 
	else:
		print "-o value is wrong; valid values are 'text' or 'html'"
		usage()
		sys.exit(2)		

if __name__ == "__main__":
	try:
		opts,args = getopt.getopt(sys.argv[1:], "o:w:p:")
	except getopt.GetoptError as err:
		print(err)
		usage()
		sys.exit(2)
	
	path = "."
	outputter = StdoutOutputter() 
	format_maker = lambda(o) : TextTreeFormatter(o)
	for o,val in opts:
		if o == "-p":
			path = val
		elif o == "-o":
			format_maker = try_get_format_maker(val)
		elif o == "-w":
			outputter = FileOutputter(val)			
		else:
			print "invalid value: " + o
			usage()
			sys.exit(2)
	path = os.path.abspath(path)
	validate_path(path)
	formatter = format_maker(outputter)
	print_tree(path, formatter)

