"""
TOKENIZER/LEXER CREATES "TOKENS" FROM A SCRIPT
"""

# reserved symbols and keywords in the language
reservedTokens = {
  # Misc
  ' ': 'whitespace',
  '\n': 'nl',
  '\\': 'escNxt',   #single \ to escape next char
  '#': 'lnCmt',    #single line comment
  '/*': 'cmtStrt',  #multi-line comment
  '*/': 'cmtEnd',

  # Expression
  '@': 'exprStrt',    #special char to start expr
  ';': 'exprEnd',     #ends expr immediately
  ',': 'exprDlm',     #delims args in expr
  '.': 'methStrt',    #start of a method (ie @bar.kill() where kill is method)

  # Structure
  '(': 'parenOpn',    #used for args
  ')': 'parenCls',  
  '{': 'braceOpn',    #used for defs
  '}': 'braceCls',  
  '[': 'bracketOpn',  #used for data
  ']': 'bracketCls',
  '\'': 'apos',       #used for strings
  '"': 'quote',       #used for strings

  # Comparison
  '<': 'lsThan',      
  '>': 'gtThan',
  '>=': 'gtThanEqTo',
  '<=': 'lsThanEqTo',
  '==': 'eqTo',             #compare
  '!==': 'notEqTo',         #compare NOT
  '===': 'eqToStrict',      #compare strict
  '!===': 'notEqToStrict',  #comapre strict NOT

  # Binary Comparison
  '!': 'binCmpr',               #NOT - eval to inverse
  '&&': 'binCmpr',              #AND - both in comparison eval to true
  #NAND = !(var1 && var 2)  #NAND - intentionally excluded for simplicity
  '||': 'binCmpr',               #OR - either in comparison eval to true
  #NOR = !(var1 || var 2)   #NOR - intentionally excluded for simplicity
  'x||': 'binCmpr',             #XOR - both in comparison are different
  #XNOR = !(var1 x|| var 2) #XNOR -intentionally excluded for simplicity

  # Binary-ish Comparison
  'all': 'ref',       #@all() - ie several chained &&    
  'any': 'ref',       #several chained ||
  'either': 'ref',    #like any but only two expressions
  'none': 'ref',      #!(@any)
  'neither': 'ref',   #like none but only two expressions
  'not': 'ref',       #same as !() but as reference
  'iv': 'ref',        #value is non-null, non-blank
  'nv': 'ref',        #value is null or blank

  # Operators
  '+': 'op',    
  '-': 'op',    
  '*': 'op',    
  '/': 'op',    
  '**': 'op',   #power
  '//': 'op',   #root
  '%': 'op',    #modulo
  '+=': 'op',   
  '-=': 'op',   
  '*=': 'op',   
  '/=': 'op',   
  '=': 'op',    #assign

  # Keywords (reserved references)
  'abort': 'ref',     #kill entire response w/o sending anything
  'stop': 'ref',      #stop further addition to response... parse it and send
  'cookie': 'ref',    #assign a cookie to client
  'httpGET': 'ref',   #try to get data from somewhere
  'httpPOST': 'ref',  #post something somewhere
  'output': 'ref',    #sets the current output value
  'sleep': 'ref',     #sleep? should this be in lang?
  'wait': 'ref',      #wait? should this be in lang?

  'rspns_header': 'ref',
  'rspns_redir': 'ref',

  'calc': 'ref',
  'min': 'ref',
  'max': 'ref',

  'chr': 'ref',
  'ord': 'ref',

  'date': 'ref',    #@date(12/25/2025 13:05:17:999) returns date as float ... @now() if no arg
  'now': 'ref',     #datetime right now as float
  'today': 'ref',   #date with 00:00:00 time as float

  'guid': 'ref',    #returns global identifier string
  'random': 'ref',  #@random(967) returns int 0-967 ... @random(451.07) returns float 0.00-451.07 

  'func': 'ref',
  'getglobal': 'ref', #gets a module level or global var for the function
  'print': 'ref',
  'return': 'ref',

  'type': 'ref',
  'class': 'ref',
  'object': 'ref',
  'this': 'ref',
  'self': 'ref',

  'library': 'ref',
  'mode': 'ref',
  'module': 'ref',

  'if': 'ref',        #ternary
  'ifTrue': 'ref',    #execute def if expr evals to true
  'ifFalse': 'ref',   #execute def if expr evals to false
  'switch': 'ref',    #switch block
  'when': 'ref',      #when the expr in switch evals to this
  'else': 'ref',      #when the expr in switch evals to none of the whens

  'const': 'ref',     #immutable, non-reassignable var
  'global': 'ref',    #makes a variable or const accessible across all modules
  'var': 'ref',       #mutable unless type explicitly stated in declaration

  # Types
  'blank': 'type',    #value is "empty" or "blank"
  'null': 'type',     #has no value, not even blank
  'variant': 'type',  #a generic type that will attempt to determine the actual type when called
  'str': 'type',
    
  'array': 'type',      #data structure array
  'dict': 'type',       #data structure dictionary
  'reference': 'type',  #points to another expression
    
  'bool': 'type',
  'datetime': 'type',
  'int': 'type',      #trunc decimals to make whole number
  'float': 'type',
  'double': 'type',   #subtype of float... currently no difference)
  'money': 'type',    #subtype of float... returns 0.00 format

  'base64': 'type',   #encoded data in base64
  'binary': 'type',   #encoded data in binary
  'hex': 'type',      #encoded data in hex
  'utf8': 'type',     #encoded data in UTF8
    
  # Special Args (args to modify behavior of expression)
  'disable': 'spArg',
  'nointerpret': 'spArg',
  'protected': 'spArg',
}

# these tokens are concatted instead
stringDelimTokens = {
  "'",  # start or end of a string
  '"',
}

# these tokens require additional processing to determine if they are comparison operators or xml/html
xmlDelimTokens = {
  '<',  # possible xml open-tag start
  '>',  # possible xml open-tag end
  '/>', # xml open-tag self-close
  '/',  # first char in /> ... 
  '</', # xml close-tag start
  #<p>...</p>
  #<img .../>
}





# the stack all tokens are stored in
class tokenStack:
  def __init__(self):
    # [[lineNumber, tokenType, tokenValue], ..., ...]
    self.stack = []

  # add token to end of stack
  def insert(self, lineNumber, tokenType, tokenValue):
    #print(f"Stored token", lineNumber, tokenType, tokenValue)
    self.stack.insert(len(self.stack), [int(lineNumber), tokenType.strip(), tokenValue.strip()])
    return
  
  # remove first token from stack
  def pop(self):
    self.stack.pop(0)
  
  # return first token in stack
  def readCurrentToken(self):
    return self.stack[0]
  
tokenStack = tokenStack()
  




# process to tokenize a submitted script
def tokenizeScript(script, scriptName:str = "Unknown Nexus Module"):
  print(f"{script}\n\n\n")

  global currentToken
  global reservedTokens
  global stringDelimTokens
  global xmlDelimTokens

  currentToken = None
  tokenLineNumber = 1
  processingStr = False
  processingXML = False

  scriptLen = len(script) # total length of the script
  pos = 0                 # position where is being processed

  # gets and returns the next token
  def getToken():
    nonlocal script
    nonlocal tokenLineNumber
    nonlocal processingStr
    nonlocal processingXML

    aToken = script[pos]
    
    # new-line = inc line number
    if aToken == '\n':
      tokenLineNumber += 1
      return aToken

    # this is the start of a string
    elif aToken in stringDelimTokens:
      # get entire string
      endPos = script.find(aToken, pos + 1)
      aToken = script[pos:endPos]
      return aToken

    # this token is either XML or comparison
    elif aToken in xmlDelimTokens:
      ...#get info abt if this is comparison or xml


    # reserved single char token (including space delim)
    elif aToken in reservedTokens:
      return aToken

    # multi-character reserved or generic arg...
    else:
      # get entire token
      endPos = script.find(' ', pos + 1)
      aToken = script[pos:endPos]
      return aToken


  # insert a start of script token
  tokenStack.insert(0, 'scptStrt', '')



  while True:
  # PROCESS SCRIPT INTO TOKENS
    
    # new token
    if currentToken is None:
      currentToken = getToken()

      # space character delims tokens
      if currentToken == ' ':
        pos += 1
        continue

      # the currentToken is a reserved token and needs to be stored
      if currentToken in reservedTokens:
        print(f"Stored token as reserved token {reservedTokens[currentToken]} {currentToken}")
        tokenStack.insert(tokenLineNumber, reservedTokens[currentToken], currentToken)
        pos += len(currentToken)
        continue

      # this is a string
      elif currentToken[0] in stringDelimTokens:
        print(f"Stored token as string arg {currentToken}")
        tokenStack.insert(tokenLineNumber, "arg", {currentToken})
        pos += len(currentToken)
        continue


      ... # OTHER TOKEN STORE PROCEDURES

      
    pos +=1
    # full script has been processed
    if pos >= scriptLen:
      break



  # insert an end of script token
  tokenStack.insert(0, 'scptEnd', '')
  
  print("TOKEN STACK:\n")
  for item in tokenStack.stack:
    print(item)

