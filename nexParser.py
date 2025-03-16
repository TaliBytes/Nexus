"""
PARSER MAKES NODES FROM TOKENS AND POPULATES ABSTRACT SYNTAX TREE (AST)
RETURNS AST OBJECT FROM TOKEN OBJECT
"""

import json
import nexServerGlobals
allReservedTokens = nexServerGlobals.allReservedTokens
exprTypeTokens = nexServerGlobals.exprTypeTokens
stringDelimTokens = nexServerGlobals.stringDelimTokens
xmlDelimTokens = nexServerGlobals.stringDelimTokens
refTokens = nexServerGlobals.refTokens





class abstractSyntaxTree:
  def __init__(self):
    self.tree = {}

  def update(self, aNode:dict):
    """Accepts dictionary that is updated/appened to the AST"""
    #print(f"Stored parsed node: {aNode}")
    self.tree.update(aNode)

  def clear(self):
    """Clears entire AST"""
    self.tree.clear()

AST = abstractSyntaxTree()





# PARSE TOKENS from tokenizeScript returned object... NEXPARSER ENTRY POINT
# Returns an Abstract Syntax Tree (AST) as object
def parseTokens(tokenStack:object)->object:
  """Initialize the parsing of tokens"""
  #global allReservedTokens
  #global exprTypeTokens
  #global stringDelimTokens
  #global xmlDelimTokens
  #global refTokens

  currentNode:dict = {}       # temp container for current node to be stored
  nodeID:int = 0              # unique id for each node
  # parts of a token
  lastToken:list = None       # lastToken is a list formatted same as currentToken
  currentToken:list = None    # currentToken[0] is lineNumber, [1] is tokenType, [2] is tokenValue
  tokenLineNumber:int = None  # currentToken[0]
  tokenType:str = None        # currentToken[1]
  tokenValue:any = None       # currentToken[2]



  def getNextToken() -> None:
    """Clear currentToken data and advance to the next token if it exists"""
    nonlocal tokenStack, lastToken, currentToken, tokenLineNumber, tokenType, tokenValue

    # clean the token data
    lastToken = currentToken  # move current token to last token
    currentToken = None
    tokenLineNumber = None
    tokenType = None
    tokenValue = None

    # only attempt to process next token if it actually exists
    if len(tokenStack.stack) > 0:
      # get next token's data and pop so it isn't reprocessed
      currentToken = tokenStack.readCurrentToken()
      tokenLineNumber = currentToken[0]
      tokenType = currentToken[1]
      tokenValue = currentToken[2]
      tokenStack.pop()
    else:
      raise Exception('Expected more tokens but the token stack is empty.')



  def peakNextTokenType()->str:
    """Peak at the next token type without advancing the stack"""
    if len(tokenStack.stack) > 0: return(tokenStack.stack[0][1])
    else: return(None)
  


  def peakNextTokenValue()->str:
    """Peak at the next token value without advancing the stack"""
    if len(tokenStack.stack) > 0: return(tokenStack.stack[0][2])
    else: return(None)
  


  def peakLastTokenType()->str:
    """Peak at the previous token type without altering the stack"""
    return(lastToken[1])



  def getNode() -> dict:
    """Returns all of the information about a node, by processing up the tokenStack starting at the bottom tokenStack.stack[0]"""
    nonlocal tokenStack, currentToken, tokenLineNumber, tokenType, tokenValue
    nonlocal nodeID

    nodeID += 1             # inc to next nodeID
    thisNodeID = None       # thisNodeID is used when storing nested nodes to a parent node... thisNodeID is the parent's nodeID
    nodeType:str = None     # ie ref, type, op, etc
    nodeRef:str = None      # ie var, def, calc, etc
    nodeName:str = None     # ie var BAR, def FOO class AST (bar, foo, ast)
    nodeLine:int = None     # line number
    nodeArgs:dict = {}      # any args that node needs to function... non-iterative and applies only to this node
    nodeBody:dict = {}      # child nodes (eg function definition... iterative and can be many layers deep)



    def formattedNode(thisNodeID:int=nodeID):
      """Formats the node into a dictionary"""
      nonlocal nodeID, nodeType, nodeRef, nodeName, nodeLine, nodeArgs, nodeBody
      return({f"{thisNodeID}": {"nodeType": nodeType, "nodeRef": nodeRef, "nodeName": nodeName, "nodeLineNumber": nodeLine, "nodeArgs": nodeArgs, "nodeBody": nodeBody}})

    

    def getTypes()->list:
      """Gets all the immediately following type declarations for vars, consts, functions, etc"""
      typeList:list = []

      # check that next token is of type EXPRTYPE (:)
      if not peakNextTokenType() == "EXPRTYPE":
        raise Exception(f"Syntax Error: Expecting TYPE-INDICATOR (:) but found {tokenValue}({tokenType}).")
      else:
        getNextToken()  # eat EXPRTYPE (:)
      
      # TYPE-INDICATOR was found, meaning the loop for finding types can be initiated
      while True:    
        getNextToken()  # the exprType token doesn't contain the type itself, so skip it

        if tokenType == "TYPE":
          typeList.append(tokenValue)
          if peakNextTokenType() in ["EXPRTYPE", "TYPE"]:
            getNextToken()
          else:
            break # exit once the next token isn't related to types
          
        else: 
          raise Exception(f"{tokenValue}({tokenType}) is not a valid type.")
        
      return(typeList)
    


    def getParams()->dict:
      """Gets all params/args for an expression declaration or call"""
      paramDict:dict = {}
      
      processTokens = True if peakNextTokenType() == "PARENOPN" else False  # should tokens be processed?
      if processTokens:
        getNextToken()  # eat parenopn so it isn't added to
        while True:
          if peakNextTokenType() == "PARENCLS":
            getNextToken()  # eat parencls so it isn't added to AST
            break
          else:
            paramDict.update(getNode()) # add this node as a param

      return(paramDict)
       


    # get the next token to process into the node
    if peakNextTokenType() != None:
      getNextToken()
    else: tokenType = None

    # since there are no more tokens, this node needs to be returned empty
    if tokenType == None:
      thisNodeID = 0
      nodeType = None
      nodeRef = None
      nodeName = None
      nodeLine = None
      nodeArgs = None
      nodeBody = None
      return(formattedNode())


    # start of script
    elif tokenType == 'SCPTSTRT':
      thisNodeID = nodeID     # preserveNodeID
      nodeType = tokenType    # start of script
      nodeRef = None          # override to no ref
      nodeName = None         # override to no name
      nodeLine = 0            # override to line 0
      nodeArgs = {}           # override to no args
    
      # start getting child nodes and appending them to body using [dict].update(...)
      while len(tokenStack.stack) > 0:
        nodeBody.update(getNode())  # scptstrt is root of AST ... body is all other nodes as children ... this is iterative


    # end of script
    elif tokenType == "SCPTEND":
      nodeType = tokenType    # end of script
      nodeRef = None          # override to no ref
      nodeName = None         # override to no name
      nodeLine = tokenLineNumber
      nodeArgs = {}           # override to no args
      nodeBody = {}           # override to no body



    # start of an expression
    elif tokenType == "EXPRSTRT":
      thisNodeID = nodeID
      nodeType = tokenType
      nodeRef = None
      nodeName = None
      nodeLine = tokenLineNumber
      nodeArgs = {}

      # all following nodes are children until this expression ends
      while True:
        if tokenType == "EXPREND": break
        nodeBody.update(getNode())
    

    # end of expression
    elif tokenType == "EXPREND":
      nodeType = tokenType
      nodeRef = tokenValue
      nodeName = None
      nodeLine = tokenLineNumber
      nodeArgs = {}
      nodeBody = {}



    # start of a string
    elif tokenType == "STRSTRT":
      thisNodeID = nodeID
      nodeType = tokenType
      nodeRef = None
      nodeName = None
      nodeLine = tokenLineNumber
      nodeArgs = {}

      # all following nodes are children until this string ends
      while True:
        if tokenType == "STREND": break
        nodeBody.update(getNode())
    

    # end of string
    elif tokenType == "STREND":
      nodeType = tokenType
      nodeRef = None
      nodeName = None
      nodeLine = tokenLineNumber
      nodeArgs = {}
      nodeBody = {}


    # for built in expressions such as var, def, class, etc
    elif tokenType == "REF":
      """
      List of built-in ref-typed expressions
      iv, nv, abort, stop, cookie, httpget, httppost, output, sleep, wait, rspns_header, rspns_redir,
      calc, min, max, chr, ord, date, now, today, guid, random,
      def, getglobal, nonlocal, print, return, class, object, self, library, use
      tern, if, switch, when, else, const, var
      """
      
      match tokenValue:
        case "IV":
          """
          example: @iv(1); @iv(@someVar);
          returns true if expression evaluates to true
          """
          thisNodeID = nodeID
          nodeType = "REF"
          nodeRef = "IV"
          nodeName = "ISVALID"
          nodeLine = tokenLineNumber
          nodeArgs = {}
          nodeArgs.update({"params":getParams()})
          nodeBody = {}
          

        case "NV":
          """
          example: @nv(1); @nv(@someVar);
          returns true true if expression evaluates to false
          """
          thisNodeID = nodeID
          nodeType = "REF"
          nodeRef = "IV"
          nodeName = "ISVALID"
          nodeLine = tokenLineNumber
          nodeArgs = {}
          nodeArgs.update({"params":getParams()})
          nodeBody = {}
          

        #case "ABORT":


        #case "STOP":


        #case "COOKIE":


        #case "HTTPGET":


        #case "HTTPPOST":


        #case "OUTPUT":


        #case "SLEEP":


        #case "WAIT":


        #case "RSPNS_HEADER":


        #case "RSPNS_REDIR":


        #case "CALC":


        #case "MIN":


        #case "MAX":


        #case "CHR":


        #case "ORD":


        #case "DATE":


        #case "NOW":


        #case "TODAY":


        #case "GUID":


        #case "RANDOM":


        #case "DEF":


        #case "GETGLOBAL":


        #case "NONLOCAL":


        #case "PRINT":


        #case "RETURN":


        #case "CLASS":


        #case "OBJECT":


        #case "SELF":


        #case "LIBRARY":


        #case "USE":


        #case "TERN":


        #case "IF":


        #case "SWITCH":


        #case "WHEN":


        #case "ELSE":


        case "CONST":
          """
          example: @const bar:int = 5;
          @const [name]:[type] = [value];
          """
          thisNodeID = nodeID     # preserveNodeID
          nodeType = "REF"
          nodeRef = "CONST"
          #nodeName
          nodeLine = tokenLineNumber
          nodeArgs = {}
          nodeBody = {}
         
          # next token must be arg [nodeName]
          if peakNextTokenType() == "ARG":
            getNextToken()
            nodeName = tokenValue
          else:
            raise Exception(f"@CONST expecting argument NAME but found {tokenValue}({tokenType}).")
          
          # const expression does not require getParams()
          # next part of syntax is always :[TYPE] (exactly one, not "any"-type)
          nodeArgs.update({"returnTypes":getTypes()})

          # exactly one type
          if len(nodeArgs['returnTypes']) > 1 or len(nodeArgs['returnTypes']) == 0:
            raise Exception(f"@CONST expecting exactly ONE type but found {len(nodeArgs['returnTypes'])} types.")
          
          # type can't be "ANY"
          if nodeArgs['returnTypes'][0] == "ANY":
            raise Exception(f"@CONST cannot be of type ANY.")
          
          # must have a value assigned immediately
          if peakNextTokenValue() != "=": # using nextTokenValue since there are many types of OP tokenTypes but only one is allowed
            raise Exception(f"@CONST expecting ASSIGNMENT (=) but found {peakNextTokenValue()}({peakNextTokenType()}).")

               
        case "VAR":
          """
          example: @var bar:int = 5;
          @var [name]:[type] [(optional) = [value]];
          """
          thisNodeID = nodeID     # preserveNodeID
          nodeType = "REF"
          nodeRef = "VAR"
          #nodeName
          nodeLine = tokenLineNumber
          nodeArgs = {}
          nodeBody = {}
         
          # next token must be arg [nodeName]
          if peakNextTokenType() == "ARG":
            getNextToken()
            nodeName = tokenValue
          else:
            raise Exception(f"@VAR expecting argument NAME but found {tokenValue}({tokenType}).")
          
          # var expression does not require getParams()               
          # next part of syntax is always :[TYPE] ... or multiple types (the types the variable can be, ie returnTypes)
          nodeArgs.update({"returnTypes":getTypes()})
          
          if peakNextTokenType() not in ["OP", "EXPREND"]:
            raise Exception(f"@VAR expecting ASSIGNMENT (=) or END (;) but found {peakNextTokenValue()}({peakNextTokenType()}).")


        # Other REF-typed tokens
        case _:
          print(f"Parser Warning B - REF-typed token {tokenValue} is not implemented in parser yet. Attempted to create node anyway.")
          nodeType = tokenType
          nodeRef = tokenValue
          nodeName = "MISSING"
          nodeLine = tokenLineNumber
          nodeArgs = {}
          nodeBody = {}

      # at this point an end of expression is always expected ... if expression end is missing, add it
      if peakNextTokenType() != "EXPREND":
        tokenStack.insert(tokenLineNumber, "EXPREND", ";", 0)

        
    # for built in operators such as +, =, etc
    elif tokenType == "OP":
      """
      List of built in operators:
      +, -, *, /, **, //, %, +=, -=, *=, /=, =
      """
      match tokenValue:
        #case "+":
        #  """Adds right value to left value"""


        #case "-":
        #  """Subtracts right value from left value"""


        #case "*":
        #  """Multiplies left value by right value"""


        #case "/":
        #  """Divides left value by right value"""


        #case "**":
        #  """Raises left value to power of right value"""


        #case "//":
        #  """nth root of left value (where n is right value)"""


        #case "%":
        #  """Modulates left value by right value"""


        #case "+=":
        #  """Adds right value to left expression value and assigns result to left expression"""


        #case "-=":
        #  """Subtracts right value from left expression value and assigns result to left expression"""


        #case "*=":
        #  """Multiplies left expression value by right value and assigns result to left expression"""


        #case "/=":
        #  """Divides left expression value by right value and assigns result to left expression"""


        case "=":
          """Assigns right value to left expression"""
          nodeType = tokenType
          nodeRef = tokenValue
          nodeName = "EQUALS"
          nodeLine = tokenLineNumber
          nodeArgs = {}
          nodeBody = {}


        case _:
          print(f"Parser Warning C - {tokenValue} ({tokenType}) not implemented in parser yet. Attempted to create node anyway.")
          nodeType = tokenType
          nodeRef = tokenValue
          nodeName = None
          nodeLine = tokenLineNumber
          nodeArgs = {}
          nodeBody = {}


    # for generic arg-typed tokens
    elif tokenType == "ARG":
      # this is a user defined function, object, or variable call
      if peakLastTokenType() == "EXPRSTRT":
        thisNodeID = nodeID
        nodeType = "REF"
        nodeRef = "ARG"
        nodeName = tokenValue
        nodeLine = tokenLineNumber
        nodeArgs.update({"params":getParams()})
        nodeBody = {} # empty or attached methods

        # get attached methods
        while True:
          if peakNextTokenType() != "METHSTRT": break
          else: nodeBody.update(getNode())

        # end of methods implies end of expression ... if expression end is missing, add it
        if peakNextTokenType() != "EXPREND":
          tokenStack.insert(tokenLineNumber, "EXPREND", ";", 0)
        
      # generic arg (such as literals, strings, etc)
      elif peakLastTokenType() != "EXPRSTRT":  
        nodeType = "ARG"
        nodeRef = "ARG"
        nodeName = "LITERAL"
        nodeLine = tokenLineNumber
        nodeArgs.update({"value":tokenValue})
        nodeBody = {} # this will always be empty for generic args as they never have bodies/children


    elif tokenType == "METHSTRT":
      # format: @expr.meth().meth().meth()...
      thisNodeID = nodeID
      nodeType = tokenType
      nodeRef = tokenValue
      #nodeName
      nodeLine = tokenLineNumber
      nodeArgs = {}
      nodeBody = {}

      # next token must be arg [nodeName]
      if peakNextTokenType() == "ARG":
        getNextToken()
        nodeName = tokenValue
      else:
        raise Exception(f"METHOD expecting NAME but found {tokenValue}({tokenType}).")
      
      # next token must be args (even if none/null/blank are supplied)
      nodeArgs.update({"params":getParams()})
      

    # catch-all for missing items
    else:
      print(f"Parser Warning A - {tokenValue} ({tokenType}) not implemented in parser yet. Attempted to create node anyway.")
      nodeType = tokenType
      nodeRef = None
      nodeName = tokenValue
      nodeLine = tokenLineNumber
      nodeArgs = {}
      nodeBody = {}



    # RUNS AFTER THE IF/ELSE STATEMENT FOR PARSING NODES BASED ON TOKEN TYPES
    thisNodeID = nodeID if thisNodeID is None else thisNodeID   # is nodeID unless a value is assigned
    return(formattedNode(thisNodeID))
      


  # initialize the building of the node tree
  if currentNode is None:
    currentNode = getNode()



  # continue looping until end of token stack 
  while len(tokenStack.stack) > 0:
    currentNode = getNode()   # get the next node
    AST.update(currentNode)   # put into tree
    currentNode = None        # reset for next node

  print(json.dumps(AST.tree, indent=2))
  return (AST)
