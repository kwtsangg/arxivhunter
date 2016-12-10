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
"""
Description="""
       A program to create an arxiv table to easy access.

       Example Usage
         1) arxivhunter -a <index> -cm <comment>     Add content based on the arxiv index
         2) arxivhunter -rm <index1> <index2>        Remove content based on the arxiv index
         3) arxivhunter -ed <index> -cm <NewComment> Remove content and add it back with new comment
         3) arxivhunter                              View the table by opening firefox
       """
"""
  History:
       2016-Dec-10 First version.
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
        self.author.append(self.getcontent("//meta/@content")[i])
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
#def printf(string, printtype="message", askforinput=False):
#  """
#    To print out the message of different types.
#    Optional: "askforinput", if true, the function will return the input by user.
#  """
#  if askforinput == False:
#    print "log %7s :: %s" % ( printtype, string )
#  elif askforinput == True:
#    return raw_input( "log %7s :: %s" % ( printtype, string ) )
#  else:
#    printf("Unknown option for askforinput in the printf function ! Exiting ...", "error")
#    sys.exit()

def update_maintex():
  maintex = open(ArxivDirPath+"/arxivhunter.tex","w+")
  print_header(maintex)
  
  for file in os.listdir(ArxivDirPath+"/data"):
    if os.path.getsize(ArxivDirPath+"/data/"+file+"/"+file+".txt") > 0:
      print_table_header(maintex, file.replace('_',' '))
      itertex = open(ArxivDirPath+"/data/"+file+"/"+file+".txt",'r')
      for line in itertex:
        maintex.write('%s\n' % (r"\hline"))
        maintex.write("%s\n" % line)
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
#      printf("Deleting %s ..." % item, "verbose") if args.verbose else None
      subprocess.check_call("rm " + item, stdout=subprocess.PIPE, shell=True)    

def add_content(ArgsAdd, Comment):
# TODO: Check the index doesnt exist before adding to the list
  item = Arxiv(ArgsAdd)
  RelDataPath   = item.category.replace(' ','_').replace('(','').replace(')','')
  subprocess.check_call("mkdir -p %s/data/%s" % (ArxivDirPath,RelDataPath), stdout=subprocess.PIPE, shell=True)
  DataTxtObject = open(ArxivDirPath+"/data/"+RelDataPath+"/"+RelDataPath+".txt",'a+')
  # index, title, author, comment. link, pdflink
  DataTxtObject.write(r"%s & %s & %s & %s & \href{%s}{arxiv} & \href{%s}{pdf} \\" % (item.index,item.title,item.authorlist,Comment,item.link,item.pdflink))
  DataTxtObject.close()

def remove_content(ArgsRemove):
  for item in ArgsRemove:
    arxiv_item = Arxiv(item)
    RelDataPath   = arxiv_item.category.replace(' ','_').replace('(','').replace(')','')
    DataTxtObject = open(ArxivDirPath+"/data/"+RelDataPath+"/"+RelDataPath+".txt",'r+')
    Output = []
    for line in DataTxtObject:
      if not re.split(' & ',line)[0] in item:
        Output.append(line)
    DataTxtObject.close()
    DataTxtObject = open(ArxivDirPath+"/data/"+RelDataPath+"/"+RelDataPath+".txt",'w+')
    DataTxtObject.writelines(Output)
    DataTxtObject.close()
  
def edit_comment(ArgsEdit, Comment):
  remove_content([ArgsEdit])
  add_content(ArgsEdit, Comment)
  
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
  file.write('%s\n' % (r"\begin{document}"))

def print_table_header(file, caption):
  file.write('%s\n' % (r"\begin{table}"))
  file.write('%s\n' % (r"\caption{"+caption+"}"))
  file.write('%s\n' % (r"\begin{tabular}{|m{2cm}|m{9cm}|m{7cm}|m{10cm}|m{1cm}|m{1cm}|}"))
  file.write('%s\n' % (r"\hline \hline"))
  file.write('%s\n' % (r"Index & Title & Authors & Comment & Arxiv & PDF \\"))

def print_table_footer(file):
  file.write('%s\n' % (r"\hline \hline"))
  file.write('%s\n' % (r"\end{tabular}"))
  file.write('%s\n' % (r"\end{table}"))

def print_footer(file):
  file.write('%s\n' % (r"\end{document}"))

#=======================================================================================
# Main
#=======================================================================================

def main():
  if args.add:
    add_content(args.add, args.comment)
    update_maintex()
    compile_maintex()
  elif args.remove:
    remove_content(args.remove)
    update_maintex()
    compile_maintex()
  elif args.edit:
    edit_comment(args.edit, args.comment)
    update_maintex()
    compile_maintex()
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
  parser.add_argument("-ed", "--edit",                   action="store"     , help="Remove arxiv index and add it back to database. Caution: The old comment will be replaced by new comment!")
  parser.add_argument("-cm", "--comment", default="-"  , action="store"     , help="Add comment.")
  parser.add_argument(       "--compile",                action="store_true", help="Compile the tex in case you need.")
#  parser.add_argument(       "--verbose", default=False, action="store_true", help="Print more messages.")
  parser.add_argument(       "--version",                action="version", version='%(prog)s ' + __version__)
  args = parser.parse_args() 

  main()
