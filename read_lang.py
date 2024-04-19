import re

"""horrible hacked together wrapper for the match class
to provide offseting"""
class MatchWrapper:
    def __init__(self,match : re.Match,offset : int):
        self.m = match
        self.offset = offset
    def span(self,*args):
        return [x+self.offset for x in self.m.span(*args)]
#moves everything after a #
def remove_comments(data : str)->str:
    split_data = data.split("#")
    ret_val = split_data[0]
    
    #back espcape comments
    for i in range(1,len(split_data)):
        if len(split_data[i-1]) <= 0:
            break
        if split_data[i-1][-1] == "\\":
            ret_val = ret_val[0:-1] #remove the \
            ret_val += '#'+split_data[i] #add in the removed data
        else:
            #once we hit a comment ignore everything else
            break

    return ret_val

def hide_parenthasis(data : str,**kwargs)->'str':

    open_parenth = kwargs["open_parenth"] if "open_parenth" in kwargs else "["
    close_parenth = kwargs["close_parenth"] if "close_parenth" in kwargs else "]"
    replace_string = kwargs["replace_string"] if "replace_string" in kwargs else "P"

    nest_layer = 0
    was_in = False
    slices = []

    parenthasis = [   (lidx,letter == open_parenth)
        for lidx, letter
        in enumerate(data)
        if letter in [open_parenth,close_parenth]
    ]

    removal_indexes = []
    for lidx,is_open in parenthasis:
        
        if nest_layer == 0 and is_open:
            removal_indexes.append(lidx)
        elif nest_layer == 1 and not is_open:
            removal_indexes.append(lidx)
        elif nest_layer == 0 and not is_open:
            print(f"unbalenced parenthasy found at index {lidx} :: {data}")
            quit()

        if is_open: nest_layer += 1
        else: nest_layer -= 1
    
    if nest_layer != 0:
        print(f"unbalenced parenthasy! :: {data}")

    offset = 0
    mapping = []
    for i in range(0,len(removal_indexes),2):
        replace = "__"+replace_string + str(int(i/2)) + "__"
        mapping.append(data[1+removal_indexes[i]+offset : removal_indexes[i+1]+offset])
        data = data[:removal_indexes[i]+offset] + replace + data[removal_indexes[i+1]+offset+1:]
        offset += len(replace) + removal_indexes[i] - removal_indexes[i+1] - 1
    return (data,mapping)

            


#single entry in the final parse tree
class GrammerNode:
    def __init__(self,
                 token : 'ParseNode',
                 match : re.Match,
                 sub_tokens = [],
                 data : str = ""
                 ):
        self.token = token
        self.match = match
        self.data = data
        self.sub_tokens = sub_tokens
    def match_size(self)->int:
        span = self.match.span()
        return span[1] - span[0]
    
    def get_summary(self,tabs = 0)->str:
        ret_val = tabs*'|-'+self.token.name + "\n"
        ret_val += tabs*'| '+self.data + "\n"
        #ret_val += tabs*'|--'+"-"*3 + "\n"
        for t in self.sub_tokens:
            ret_val +=  t.get_summary(tabs+1)
        
        return ret_val

#represents an idea that we can place in the parse tree
class ParseNode:
    def __init__(self,name):
        self.name = name
        self.rules = []
    
    def is_lexim(self)->bool:
        for r in self.rules:
            if not type(r) == re.Pattern:
                return False
        return True
    
    def search(self,data)->'re.Match':
        if not self.is_lexim():
            return None
        for r in self.rules:
            s = r.search(data)
            if s: return s
    
    def get_lexims(self):
        if self.is_lexim():
            return [self]
        ret_val = []
        return ret_val

    def match(self,data : str)->'GrammerNode':
        #print("---")
        #print(self.name)
        #print("'"+data+"'")
        #print("---\n")
        #simply match and return if valid
        if self.is_lexim():
            for r in self.rules:
                match = re.compile("^"+r.pattern+"$").match(data)
                if match:
                    g = GrammerNode(self,match)
                    return g
            return None #this token does not match


        for _,rule in self.rules:

            #match all of the lexims first, then use those to pattern match the remaining
            #nodes
            lexim_rules = [token for token, _ in rule if token.is_lexim()]
            if len(lexim_rules) > 0:
                lexim_matches = []
                no_match : bool = False
                token_search_start = 0
                for token in lexim_rules:
                    match = token.search(data[token_search_start:])
                    if match == None: 
                        #we must match ALL lexims for there
                        #to be a valid match on this rule
                        no_match = True
                        break

                    lexim_matches.append(MatchWrapper(match, token_search_start))
                    token_search_start += match.span()[1]

                #print('lexim_matches')
                #print(lexim_matches)
                if no_match: continue

                #for each match that we have incriment the other tokens until we get up to that match
                data_index = 0
                token_index = 0
                lexim_index = 0
                span = lexim_matches[lexim_index].span()
                chunk = data[data_index:span[0]]
                matches = []



                #while data_index == span[0]:
                #    matches.append(GrammerNode(lexim_matches[lexim_index]))
                #    data_index += span[1]
                #    lexim_index += 1
                #    span = lexim_matches[lexim_index].span()


                rule_was_matched = True
                for token,start in rule:
                    
                    #print('data_index '  + str(data_index))
                    #print('token_index ' + str(token_index))
                    #print('lexim_index ' + str(lexim_index))
                    #print('span '        + str(span))
                    #print('chunk '       + str(chunk))

                    if token.is_lexim():
                        
                        #print('\tmatching a lexim node')
                        #print('\t'+token.name)

                        lexim_grammer_node = GrammerNode(token,
                                                         lexim_matches[lexim_index],
                                                         [],
                                                         data[span[0]:span[1]])

                        matches.append(lexim_grammer_node)
                        lexim_index += 1
                        data_index += lexim_grammer_node.match_size()
                        
                        if lexim_index < len(lexim_matches):
                            span = lexim_matches[lexim_index].span()
                            chunk = data[data_index:span[0]]
                        else:
                            chunk = data[lexim_grammer_node.match.span()[1]+1:]
                            span = (len(data),0)
                    else:
                        g = token.match(data[data_index:span[0]])
                        if g == None:
                            rule_was_matched = False
                            break
                            

                        data_index += g.match_size()
                        matches.append(g)
                
                if not rule_was_matched or data_index != len(data):
                    continue #move onto checking the next rule

                return GrammerNode(self,re.match('.*',data),matches,data)

            else:
                for token,_ in rule:
                    g = token.match(data)
                    if g != None: 
                        return GrammerNode(self,re.match(".*",data),[g],data)










    def __str__(self):
        ret_val = self.name + " -> "
        for r in self.rules:
            ret_val += str(r) + " , "
        return ret_val[0:-3]

#convinence class to iterate through a rule containing several mappings
class Mappings:
    def __init__(self,string : str):
        self._data = string
        self.idx = 0
    def __iter__(self):
        return self
    def __next__(self):
        work_string = self._data[self.idx:]

        if not "<" in work_string or not ">" in work_string:
            raise StopIteration
        
        start = work_string.index("<") + self.idx
        end = work_string.index(">") + self.idx
        self.idx = end + 1

        return (self._data[start+1:end],start,end)

class LanguageMap:
    def __init__(self,map_nodes,entry_node):
        self.rule_mesh = map_nodes
        self.entry_node = entry_node
    
    @staticmethod
    def from_file(lang_file_path : str,entry_point : str='statement')->'LanguageMap':
        data = get_parse_dictionary(lang_file_path)
        
        lexims = get_lexims(data)
        maps = get_mappings(data)

        lexim_nodes = create_lexim_map(lexims)
        map_nodes = create_rule_map(maps)

        mesh = create_mapping_mesh(lexim_nodes,map_nodes)
        
        return (LanguageMap(mesh,map_nodes[entry_point]),lexim_nodes,map_nodes)

#generates a dictionary of rules based on a given .lang file
#very rudimentary, inteanded for further parsing
def get_parse_dictionary(path : str):
    continuation = re.compile("\\s+.+")

    ret_val = {}
    last_entry = ""
    with open(path,'r') as f:
        for line in f:
            line = remove_comments(line[:-1]) #strip new lines at the end
            
            if line == "" or line == "\n":
                continue

            if continuation.match(line):
                #include the seperator
                if ret_val[last_entry] != "": ret_val[last_entry]+= "|"

                ret_val[last_entry] += line.strip()
                continue
            
            split_data = line.split('=')
            
            
            if split_data[1] == "":
                add_to = split_data[1]

            ret_val[split_data[0]] = "=".join(split_data[1:]).strip()

            last_entry = split_data[0]
        else:
            pass
            #print("end of the file")
        
        #clean up and create lists from the initial data
        return { key.strip():ret_val[key].split("|") for key in ret_val}


#returns true if the rule can be recursed into
def has_inner_rule(rule : str)->bool:
    reg = re.compile('<.+>')
    return re.match(reg,rule)

#returns a dictionaries of lexims from the langage
def get_lexims(data):
    return {key:data[key] 
                for key in data 
                    if not any(
                            has_inner_rule(law) for law in data[key]
                            )}

#returns a dictionaries of mappings for the language
def get_mappings(data):
    return {key:data[key] 
                for key in data 
                    if any(
                            has_inner_rule(law) for law in data[key]
                            )}

#creates a maping of lexims given a dictionary of lexims
def create_lexim_map(lexims):
    ret_val = {}
    
    for key in lexims:
        lexim_node = ParseNode(key)
        for rule in lexims[key]:
            lexim_node.rules.append(re.compile(rule))
        ret_val[key] = lexim_node
    return ret_val


#generates a regex along with the mappings that the regex matches
def get_rule_mapping_data(rule):
    mappings = []
    error = 0
    for mapping,start,end in Mappings(rule):
        rule = rule[0:start-error] +".*"+rule[end-error+1:]
        mappings.append((mapping,start-error))
        error += len(mapping) #account for index differences
    return (rule,mappings)


def create_rule_map(maps):
    ret_val = {}
    
    for key in maps:
        rule_map = ParseNode(key)
        rule_map.rules = [get_rule_mapping_data(rule) for rule in maps[key]]
        ret_val[key] = rule_map

    return ret_val

#updates the mappings for a given map node to point to the mapping in a given context
def translate_mappings_to_pointers(map_node_to_translate,lexim_nodes,map_nodes):
        pointer_rule = []
        for regex,mapps in map_node_to_translate.rules:
            pointer_mapps = []
            for mapping,start in mapps:
                if mapping in map_nodes:
                    pointer_mapps.append((map_nodes[mapping],start))
                else:
                    pointer_mapps.append((lexim_nodes[mapping],start))
            pointer_rule.append((regex,pointer_mapps))
        map_node_to_translate.rules = pointer_rule

#generates a final self referential data structure
#where each node points to other nodes for a context
#free grammer
def create_mapping_mesh(lexim_nodes,map_nodes):
    #lexim nodes do not point to anything, so we can plop them right down in the data structure
    ret_val = [lexim_nodes[key] for key in lexim_nodes]

    #for the given map node, any reference of it that is inside of the new array
    for key in map_nodes:
        translate_mappings_to_pointers(map_nodes[key],lexim_nodes,map_nodes)
        ret_val.append(map_nodes[key])
    
    return ret_val



def get_token_str(node : 'GrammerNode')->str:
    if len(node.sub_tokens) == 0:
        return f"<{node.token.name}>"
    ret_val = ""
    for t in node.sub_tokens:
        ret_val += get_token_str(t)
    return ret_val


def read_without_white(f):
    return f.read(1)

if __name__ == '__main__':

    #generate the langauge structure
    l,lexims,maps = LanguageMap.from_file("example.lang",entry_point ="statement")
    any_match = False
    
    f = open('input.txt','r')
    data = read_without_white(f)
    while data != "":
        g = maps[l.entry_node.name].match(data)
        while g == None:
            d = read_without_white(f)
            data += d
            g = maps[l.entry_node.name].match(data)
            if d == "":
                data = ""
                break


        if g != None:
            print(g.get_summary())
            any_match = True
            data = f.read(1)
    
    if not any_match:
        print('invalid data, try again!')
    f.close()
