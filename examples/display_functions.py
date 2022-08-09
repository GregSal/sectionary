
# %% Function to compare context for two sections.
def compare_context(section1, section2):
    ctx_template = '{key:16s}:\t{item1:16s}\t{item2:16s}'
    context_1 = section1.context
    context_2 = section2.context
    keys_1 = set(context_1.keys())
    keys_2 = set(context_2.keys())
    all_keys = keys_1 | keys_2
    for key in all_keys:
        item1 = context_1.get(key, '')
        item2 = context_2.get(key, '')
        ctx_str = ctx_template.format(key=str(key), item1=str(item1), item2=str(item2))
        print(ctx_str)
        
        
# %% Compare Buffered Iterator contents
def buffered_iterator_compare(iter1, iter2=None, iter3=None, 
                              label1='From Iterator', 
                              label2='To Iterator', label3=''):
    
    def extract_attrs(buf_obj, requested_item, as_list=True):
        if not buf_obj:
            text = ''
        elif as_list:
            text = str(list(buf_obj.__getattribute__(requested_item)))
        else:
            text = str(buf_obj.__getattribute__(requested_item))
        return text
        
    def extract_attr_text(requested_item, iter1, iter2=None, iter3=None, 
                        as_list=True):    
        attr_text = {
            1: extract_attrs(iter1, requested_item, as_list),
            2: extract_attrs(iter2, requested_item, as_list),
            3: extract_attrs(iter3, requested_item, as_list),
        }
        return attr_text


    row_template = ''.join([
        '\t{Label:<20s}',
        '{first_iter_item:<35s}',
        '{second_iter_item:<35s}',
        '{third_iter_item:<35s}\n'
        ])   
    attr_group = {
        'Previous Items': ('previous_items', True),
        'Future Items': ('future_items', True),
        'Item Count': ('item_count', False),
        'Step Back': ('_step_back', False),
        'Buffer Size': ('buffer_size', False)
        }

    row_list = [
        row_template.format(
            Label='',
            first_iter_item=label1, 
            second_iter_item=label2, 
            third_iter_item=label3)
                ]

    for label, attr_s in attr_group.items():
        requested_item, as_list = attr_s
        text_group = extract_attr_text(requested_item, iter1, iter2, iter3, as_list)
        text_line = row_template.format(Label=label, 
                        first_iter_item=text_group[1],
                        second_iter_item=text_group[2],
                        third_iter_item=text_group[3])
        row_list.append(text_line)
    
    iterator_compare_str = ''.join(row_list)
    
    return iterator_compare_str
