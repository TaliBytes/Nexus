"""
TOKENIZER/LEXER CREATES "TOKENS" FROM A SCRIPT
"""
import nexErrHandler as neh

import nexServerGlobals
allReservedTokens = nexServerGlobals.allReservedTokens
exprTypeTokens = nexServerGlobals.exprTypeTokens
stringDelimTokens = nexServerGlobals.stringDelimTokens
xmlDelimTokens = nexServerGlobals.xmlDelimTokens
refTokens = nexServerGlobals.refTokens
methodTypes = nexServerGlobals.methodTypes





# the stack all tokens are stored in
class tokenStack:
  def __init__(self):
    # [[lineNumber, tokenType, tokenValue], .., ..]
    self.stack = []

  def insert(self, lineNumber:int, tokenType:str, tokenValue, pos:int=None):
    """Add a token at position in stack OR at top of stack if no position specified"""
    #print(f"Stored token from line", lineNumber, 'as', tokenType, tokenValue)
    position = pos if pos != None else len(self.stack)
    self.stack.insert(position, [int(lineNumber), tokenType.strip().upper(), tokenValue.strip()])
  
  def pop(self, pos:int=0):
    """Remove a token from the bottom of the stack"""
    self.stack.pop(pos)
  
  def readCurrentToken(self):
    """Return the bottom token from the stack, doesn't remove"""
    return self.stack[0]
  
  def clear(self):
    """Clears the entire token stack"""
    # the tokenStack is reused and needs to be cleared between uses
    self.stack.clear()
  
defaultStack = tokenStack()
  




def tokenizeScript(script:str, scriptName:str = "Unknown Nexus Module", tokenStack:object=defaultStack) -> object:
  """Process a script into a token stack"""
  global allReservedTokens, stringDelimTokens, xmlDelimTokens
  #global exprTypeTokens
  #global refTokens
  #global methodTypes

  currentToken:str = None
  tokenLineNumber:int = 1         # file line number for where token is at
  processingStr:bool = False      # currently processing a string token
  processingStrDelim:chr = None   # " or '
  processingFStr:bool = False     # currently processing a functional / formatted string token
  processingXML:bool = False      # currently processing an xml token

  scriptLen:int = len(script)     # total length of the script
  pos:int = 0                     # position where is being processed


  def findNextReservedSingleCharToken(searchToken:str = None) -> int:
    """Returns the position of the next single character reserved token"""
    nonlocal script
    nonlocal pos
    cursor:int = pos

    while True:
      if cursor < scriptLen:

        # searching for any reserved token
        if not searchToken:
          if script[cursor].upper() in allReservedTokens:
            break # found match
          else: cursor += 1

        # searching for a specific reserved token
        if searchToken:
          if script[cursor].upper() == searchToken:
            break # found match
          else: cursor +=1
          
      else:
        cursor = scriptLen  #end of script is last char
        break
    
    return cursor



  def getToken() -> str:
    """Finds and returns the next token"""
    nonlocal script, tokenLineNumber, processingStr, processingStrDelim, processingFStr, processingXML
    
    aToken:str = str(script[pos].upper())
    
    # new-line = inc line number
    if aToken == '\n':
      tokenLineNumber += 1
      #print(f"a. Found token newline")
      return aToken
    

    # this is the start of a string
    elif aToken in stringDelimTokens:
      # currently processing a string AND end delim match start delim .. end of string unless escaped
      if processingStr and (aToken == processingStrDelim):
        isEscaped = True if script[pos-1] == '\\' else False

        # if it is escaped, continue processing string; otherwise, is end of string
        if not isEscaped:
          processingStr = False
          processingFStr = False
          processingStrDelim = None # no longer processing

      elif not processingStr:
        processingStr = True
        processingStrDelim = aToken
        if script[pos-1].upper() == 'F':
          processingFStr = True   # this is a formatted/functional string

      #print(f"b. Found token {aToken}")
      return aToken


    # this token is either XML or comparison
    elif aToken in xmlDelimTokens:
      # +1 to get next pos, -1 to get set script last char bound
      nextChar:str = str(script[min(pos+1, scriptLen-1)]).upper()

      if nextChar not in allReservedTokens: processingXML = True            # not a comparison
      if str(aToken) + str(nextChar) in ['/>', '</']: processingXML = True  # is certainly xml
      if aToken == '/' and nextChar in ['/', '=']: processingXML = False    # /= and // are reserved
      if aToken == '/' and nextChar != '>': processingXML = False           # indicates this is a / OP

      if processingXML == False: # comparison operator
        #print(f"g. Found token {aToken}")
        return aToken

      elif processingXML == True:
        # /> (xml open-tag self-end)
        if (str(aToken) + str(nextChar) == '/>'):
          aToken = str(aToken) + str(nextChar)  # get /> instead of /
          #print(f"h. Found token {aToken}")
          return aToken
        
        # </ (xml close-tag start)
        elif (str(aToken) + str(nextChar) == '</'):
          aToken = str(aToken) + str(nextChar)  # get </ instead of <
          #print(f"h. Found token {aToken}")
          return aToken
        
        # < (xml open-tag start)
        elif aToken == '<':
          #print(f"h. Found token {aToken}")
          return aToken
        
        # > (xml tag-end)
        elif aToken == '>':
          #print(f"h. Found token {aToken}")
          return aToken

        else:
          try: raise neh.nexException(f'Failed XML token-type lookup on "{aToken}"')
          except neh.nexException as err:
            neh.nexError(err, False, scriptName, tokenLineNumber)
            processingXML = False
            return aToken


    # vanilla string
    elif processingStr and not processingFStr:     
      endPos:int = findNextReservedSingleCharToken(processingStrDelim)
      aToken = script[pos:endPos]
      #print(f"e. Found token {aToken}")
      return aToken
    

    # reserved single char token (including space delim)
    elif aToken.upper() in allReservedTokens:
      #print(f"c. Found token {aToken.replace(' ', '_')}")
      return aToken


    # functional string - tokenize each possible token in it
    elif processingStr and processingFStr:
      endPos:int = findNextReservedSingleCharToken()
      aToken = script[pos:endPos]
      #print(f"f. Found token {aToken}")
      return aToken
    

    # multi-character reserved or generic arg...
    # simply find end of this token by getting start of next
    elif not processingStr and not processingFStr:
      endPos:int = findNextReservedSingleCharToken()
      aToken = script[pos:endPos]
      #print(f"d. Found token {aToken}")
      return aToken



  # reset the stack and insert scptStrt
  tokenStack.clear()
  tokenStack.insert(0, 'scptStrt', '')



  while True:
  # PROCESS SCRIPT INTO TOKENS
    # full script has been processed
    if pos >= scriptLen:
      break
    
    # new token
    if currentToken is None:
      currentToken = getToken() # now that the token is found, the next step will store it
      #print(f"New token found: {currentToken}")
      #print(currentToken, allReservedTokens[currentToken.upper()])

      # space character delims tokens ... doesn't get stored
      if currentToken == ' ':
        pos += 1
        currentToken = None
        continue


      # the currentToken is a string delimiter
      elif currentToken in stringDelimTokens:
        # processingStr is toggled in getToken. If true, then a str just started..
        if processingStr:
          isEscaped:bool = True if script[pos-1] == '\\' else False

          if isEscaped:
            tokenStack.insert(tokenLineNumber, allReservedTokens[currentToken.upper()].upper(), currentToken.upper())
  
          elif not isEscaped:
            #print(f"Stored token as STRLITERAL {currentToken}")
            tokenStack.insert(tokenLineNumber, "STRLITERAL", currentToken.upper())

        elif not processingStr:
          #print(f"Stored token as STREND {currentToken}")
          tokenStack.insert(tokenLineNumber, "STREND", currentToken.upper())

        pos += len(currentToken)
        currentToken = None
        continue


      # the current token is an XML tag of some kind instead of comparison operator
      elif processingXML and currentToken in xmlDelimTokens:
        # /> (xml open-tag self-end)
        if (currentToken == '/>'):
          #print(f"Stored token as xmlSlfEnd {currentToken}")
          tokenStack.insert(tokenLineNumber, 'XMLSLFEND', currentToken.upper())
          processingXML = False # end of tag

        # </ (xml close-tag start)
        elif (currentToken == '</'):
          #print(f"Stored token as xmlClsStrt {currentToken}")
          tokenStack.insert(tokenLineNumber, 'XMLCLSSTRT', currentToken.upper())
          processingXML = True  # still processing

        # < (xml open-tag start)
        elif currentToken == '<':
          #print(f"Stored token as xmlOpnStrt {currentToken}")
          tokenStack.insert(tokenLineNumber, 'XMLOPNSTRT', currentToken.upper())
          processingXML = True  # still processing

        # > (xml tag-end)
        elif currentToken == '>':
          #print(f"Stored token as xmlTagEnd {currentToken}")
          tokenStack.insert(tokenLineNumber, 'XMLTAGEND', currentToken.upper())
          processingXML = False # end of tag

        pos += len(currentToken)
        currentToken = None
        continue


      # the currentToken is a reserved token and needs to be stored ... don't store new-lines
      elif currentToken.upper() in allReservedTokens:
        # new line tokens previously counted line number, but shouldn't be stored
        if allReservedTokens[currentToken.upper()].upper() == "NL":
          pos += len(currentToken)
          currentToken = None
          continue

        # handle operators differently
        elif allReservedTokens[currentToken.upper()].upper() == "OP":
          # built in operators: +, -, *, /, **, //, %, +=, -=, *=, /=, =
          if str(currentToken) + str(script[min(pos+1, scriptLen-1)]) in ['+=', '-=', '*=', '/=', '//']:  # this is a multi-char operator
            currentToken = currentToken + script[min(pos+1, scriptLen-1)] # store mutli-char operator as currentToken
              
          # store the operator token
          #print(f"Stored token as reserved token {allReservedTokens[currentToken.upper()]} {currentToken}")
          tokenStack.insert(tokenLineNumber, allReservedTokens[currentToken.upper()].upper(), currentToken.upper())
          pos += len(currentToken)
          currentToken = None
          continue
          
        else: # default reserved token procedure
          #print(f"Stored token as reserved token {allReservedTokens[currentToken.upper()]} {currentToken}")
          tokenStack.insert(tokenLineNumber, allReservedTokens[currentToken.upper()].upper(), currentToken.upper())
          pos += len(currentToken)
          currentToken = None
          continue


      # generic arg token
      else:
        #print(f"Stored token as generic arg {currentToken}")
        tokenStack.insert(tokenLineNumber, "ARG", currentToken)
        pos += len(currentToken)
        currentToken = None
        continue

  # insert an end of script token
  tokenStack.insert(tokenLineNumber + 1, 'SCPTEND', '')
  
  """
  print(f"\n{script}\n")
  """
  print("TOKEN STACK:\n")
  for item in tokenStack.stack:
    print(item)
  print('\n')


  # print tokenizer warnings then clear
  if len(neh.warnings) != 0:
    print('TOKENIZER WARNINGS:')
    for warning in neh.warnings:
      print(warning)
    neh.warnings.clear()
  
  return ((tokenStack, scriptName))
