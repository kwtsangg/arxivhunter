#!/usr/bin/env python
# -*- coding: UTF-8 -*-
__file__       = "arxivhunter"
__author__     = "Ka Wa Tsang"
__copyright__  = "Copyright 2016"
__version__    = "1.0.1"
__email__      = "kwtsang@nikhef.nl"

"""
  Name:
       arxivhunter
  Author:
       Ka Wa TSANG
  Date:
       2016-Dec-10 Birthday
"""
Description="""
       A program to create an arxiv table for easy access.

       Example Usage
         1) arxivhunter -a <index> -c <comment>      Add/Edit content based on the arxiv index
         2) arxivhunter -rm <index1> <index2>        Remove content based on the arxiv index
         3) arxivhunter                              View the table by opening firefox
       """
#=======================================================================================
# Module/package import
#=======================================================================================
import os
import sys
import argparse
import subprocess
import textwrap
from datetime import datetime
import re
import requests
from lxml import etree

#=======================================================================================
# User Input before using this scirpt !!
#=======================================================================================
# Global Variable
ArxivDirPath="/home/kwtsang/OneDrive_CUHK/mle/arxivhunter"

#=======================================================================================
# Arxiv class definition to hold all needed contents by providing index
#=======================================================================================
class Arxiv:
  def __init__(self, index):
    self.index    = index
    self.link     = "https://arxiv.org/abs/" + index
    self.html     = self.gethtml()

    self.pdflink  = "https://arxiv.org/pdf/" + index + ".pdf"
    self.category = self.getcontent("//td//span/text()")[0]
    self.abstract = self.getcontent("//blockquote/text()[last()]")[0].replace('\n','')

    self.author   = []
    for i, name in enumerate(self.getcontent("//meta/@name")):
      if name == "citation_title":
        self.title  = self.getcontent("//meta/@content")[i]
      if name == "citation_author":
        tmp_name = re.split(', ',self.getcontent("//meta/@content")[i])
        if len(tmp_name) == 1: 
          self.author.append(tmp_name[0])
        elif len(tmp_name) == 2:
          self.author.append(tmp_name[1]+" "+tmp_name[0])
        else:
          print "The author name has two commas. Strange ! Exiting ..."
          sys.exit()
      if name == "citation_date":
        self.date   = self.getcontent("//meta/@content")[i]

    self.authorlist = self.getauthorlist()

  def gethtml(self):
    return requests.get(self.link).content
  
  def getcontent(self, pattern):
    return etree.HTML(self.html).xpath(pattern)
  
  def getauthorlist(self):
    authorlist = ""
    for item in self.author:
      authorlist = authorlist + item
      if not item == self.author[-1]:
        authorlist = authorlist + ", "
    return authorlist

#=======================================================================================
# General Function
#=======================================================================================
def printf(string, printtype="message", askforinput=False):
  """
    To print out the message of different types.
    Optional: "askforinput", if true, the function will return the input by user.
  """
  if askforinput == False:
    print "Arxiv %7s :: %s" % ( printtype, string )
  elif askforinput == True:
    return raw_input( "Arxiv %7s :: %s" % ( printtype, string ) )
  else:
    printf("Unknown option for askforinput in the printf function ! Exiting ...", "error")
    sys.exit()

def query_yes_no(question, default="yes"):                                                                                                                                                                   
    """Ask a yes/no question via raw_input() and return their answer.

    "question" is a string that is presented to the user.
    "default" is the presumed answer if the user just hits <Enter>.
        It must be "yes" (the default), "no" or None (meaning
        an answer is required of the user).

    The "answer" return value is one of "yes" or "no".
    """
    valid = {"yes":"yes",   "y":"yes",  "ye":"yes",
             "no":"no",     "n":"no"}
    if default == None:
        prompt = " [y/n] "
    elif default == "yes":
        prompt = " [Y/n] "
    elif default == "no":
        prompt = " [y/N] "
    else:
        raise ValueError("invalid default answer: '%s'" % default)

    while 1:
        choice = printf(question + prompt, askforinput=True).lower()
        if default is not None and choice == '': 
            return default
        elif choice in valid.keys():
            return valid[choice]
        else:
            printf("Please respond with 'yes' or 'no' (or 'y' or 'n').", "warning")

#=======================================================================================
# Arxivhunter Function
#=======================================================================================
def update_maintex():
  maintex = open(ArxivDirPath+"/arxivhunter.tex","w+")
  print_header(maintex)
  
  for file in os.listdir(ArxivDirPath+"/data"):
    if os.path.getsize(ArxivDirPath+"/data/"+file+"/"+file+".txt") > 0:
      print_table_header(maintex, file.replace('_',' '))
      itertex = open(ArxivDirPath+"/data/"+file+"/"+file+".txt",'r')
      for line in itertex:
        maintex.write('%s\n' % (r"\hline"))
        maintex.write("%s\n" % line.replace('\n',''))
      itertex.close()
      print_table_footer(maintex)
  
  print_footer(maintex)
  maintex.close()

def compile_maintex():
  os.chdir(ArxivDirPath)
  # Compile
  subprocess.check_call("pdflatex -halt-on-error %s/arxivhunter.tex" % (ArxivDirPath), stdout=subprocess.PIPE, shell=True)
  subprocess.check_call("pdflatex -halt-on-error %s/arxivhunter.tex" % (ArxivDirPath), stdout=subprocess.PIPE, shell=True)
  # Clean
  TexCleanFileFormat=[ "log", "aux", "out", "nav", "snm", "toc", "dvi" ]
  for fileformat in TexCleanFileFormat:
    item = ArxivDirPath + "/arxivhunter." + fileformat
    if os.path.isfile(item):
      printf("Deleting %s ..." % item, "verbose") if args.verbose else None
      subprocess.check_call("rm " + item, stdout=subprocess.PIPE, shell=True)    

def add_content(ArgsAdd, Comment):
  arxiv_item = Arxiv(ArgsAdd)
  RelDataPath   = arxiv_item.category.replace(' ','_').replace('(','').replace(')','')
  subprocess.check_call("mkdir -p %s/data/%s" % (ArxivDirPath,RelDataPath), stdout=subprocess.PIPE, shell=True)
  DataTxtObject = open(ArxivDirPath+"/data/"+RelDataPath+"/"+RelDataPath+".txt",'a+')
  # index, title, author, comment. link, pdflink
  DataTxtObject.write("%s & %s & %s & %s & \href{%s}{arxiv} & \href{%s}{pdf} \\\\ \n" % (arxiv_item.index,arxiv_item.title,arxiv_item.authorlist,Comment,arxiv_item.link,arxiv_item.pdflink))
  DataTxtObject.close()

def remove_content(ArgsRemove):
  arxiv_item = Arxiv(ArgsRemove)
  RelDataPath   = arxiv_item.category.replace(' ','_').replace('(','').replace(')','')
  DataTxtObject = open(ArxivDirPath+"/data/"+RelDataPath+"/"+RelDataPath+".txt",'r+')
  Output = []
  for line in DataTxtObject:
    if not re.split(' & ',line)[0] in arxiv_item.index:
      Output.append(line)
  DataTxtObject.close()
  DataTxtObject = open(ArxivDirPath+"/data/"+RelDataPath+"/"+RelDataPath+".txt",'w+')
  DataTxtObject.writelines(Output)
  DataTxtObject.close()
  
def edit_comment(ArgsEdit, Comment):
  arxiv_item = Arxiv(ArgsEdit)
  RelDataPath   = arxiv_item.category.replace(' ','_').replace('(','').replace(')','')
  DataTxtObject = open(ArxivDirPath+"/data/"+RelDataPath+"/"+RelDataPath+".txt",'r+')
  Output = []
  for line in DataTxtObject:
    if not re.split(' & ',line)[0] == arxiv_item.index:
      Output.append(line)
    else:
      Output.append("%s & %s & %s & %s & \href{%s}{arxiv} & \href{%s}{pdf} \\\\ \n" % (arxiv.index,arxiv.title,arxiv.authorlist,Comment,arxiv.link,arxiv.pdflink))
  DataTxtObject.close()
  DataTxtObject = open(ArxivDirPath+"/data/"+RelDataPath+"/"+RelDataPath+".txt",'w+')
  DataTxtObject.writelines(Output)
  DataTxtObject.close()
  
def get_comment(index):
  """ It can be used to check the existence of index. If the index doesnt exist, return empty string.
  """
  comment = ""
  arxiv_item    = Arxiv(index)
  RelDataPath   = arxiv_item.category.replace(' ','_').replace('(','').replace(')','')
  DataTxtObject = open(ArxivDirPath+"/data/"+RelDataPath+"/"+RelDataPath+".txt",'r+')
  for line in DataTxtObject:
    if re.split(' & ',line)[0] == arxiv_item.index:
      comment = re.split(' & ',line)[3]
      break
  DataTxtObject.close()
  return comment
  

#=======================================================================================
# Template Function
#=======================================================================================
def print_header(file):
  file.write('%s\n' % (r"\documentclass{article}"))
  file.write('%s\n' % (r"\usepackage[paperheight=8.5in,paperwidth=13.0in,margin=0.1in,headheight=0.0in,footskip=0.5in,includehead,includefoot]{geometry}"))
  file.write('%s\n' % (r"\usepackage{hyperref}"))
  file.write('%s\n' % (r"\usepackage{amsmath}"))
  file.write('%s\n' % (r"\usepackage{physics}"))
  file.write('%s\n' % (r"\usepackage{array}"))
  file.write('%s\n' % (r"\usepackage{longtable}"))
  file.write('%s\n' % (r"\title{Arxiv table}"))
  file.write('%s\n' % (r"\author{" + __author__ +  "}"))
  file.write('%s\n' % (r"\date{\today}"))  
  file.write('%s\n' % (r"\begin{document}"))
  file.write('%s\n' % (r"\maketitle"))

def print_table_header(file, caption):
  file.write('%s\n' % (r"\section{"+caption+"}"))
  file.write('%s\n' % (r"\begin{longtable}{|m{2cm}|m{9cm}|m{7cm}|m{10cm}|m{1cm}|m{1cm}|}"))
  file.write('%s\n' % (r"\hline \hline"))
  file.write('%s\n' % (r"Index & Title & Authors & Comment & Arxiv & PDF \\"))

def print_table_footer(file):
  file.write('%s\n' % (r"\hline \hline"))
  file.write('%s\n' % (r"\end{longtable}"))

def print_footer(file):
  file.write('%s\n' % (r"\end{document}"))

#=======================================================================================
# Main
#=======================================================================================

def main():
  if args.add:
    if get_comment(args.add) == "":
      printf("The index %s doesnt exist. Adding ..." % args.add)
      add_content(args.add, args.comment)
    else:
      printf("The index %s exists already." % args.add)
      printf("The current comment is : %s" % get_comment(args.add))
      printf("The   input comment is : %s" % args.comment)
      if query_yes_no("Do you want to replace the current comment by the input comment?", default="no") == "yes":
        edit_comment(args.add, args.comment)
      else:
        printf("Exiting ...")
        sys.exit()
    update_maintex()
    compile_maintex()
  elif args.remove:
    for item in args.remove:
      printf("Removing index %s ..." % item)
      remove_content(item)
    update_maintex()
    compile_maintex()
  elif args.update:
    update_maintex()
  elif args.compile:
    compile_maintex()
  else:
    subprocess.check_call("firefox %s/arxivhunter.pdf" % ArxivDirPath, stdout=subprocess.PIPE, shell=True)

if __name__ == "__main__":
  # Fix UnicodeEncodeError
  reload(sys)
  sys.setdefaultencoding('utf-8')
  
  parser = argparse.ArgumentParser(description=textwrap.dedent(Description), prog=__file__, formatter_class=argparse.RawTextHelpFormatter)
  parser.add_argument("-a ", "--add",                    action="store"     , help="Add arxiv index to database")
  parser.add_argument("-rm", "--remove", nargs="+",      action="store"     , help="Remove arxiv index to database")
  parser.add_argument("-c ", "--comment", default="-"  , action="store"     , help="Add comment.")
  parser.add_argument(       "--compile",                action="store_true", help="Compile the tex in case you need.")
  parser.add_argument(       "--update",                 action="store_true", help="Update the tex in case you need.")
  parser.add_argument(       "--verbose", default=False, action="store_true", help="Print more messages.")
  parser.add_argument(       "--version",                action="version", version='%(prog)s ' + __version__)
  args = parser.parse_args() 

  main()
