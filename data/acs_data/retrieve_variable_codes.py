import pandas as pd

def input_prompt():
    '''Prompt user to input table ID and label's components'''
    data_year = input('Data year:')
    acs_estimate = input('ACS estimate type (Enter 1 for 1-year estimate or 5 for 5-year estimate):')
    table_id = input('Table ID:')
    parent_col = input('Parent column:')
    child_col = input('Child column:')
    parent_label = input('Parent label:')
    child_label_1 = input('Child label 1:')
    child_label_2 = input('Child label 2:')
    child_label_3 = input('Child label 3:')

    # A list of label's components
    label_components = [child_col, parent_col, parent_label, child_label_1, child_label_2, child_label_3]

    return data_year, acs_estimate, table_id, label_components

def get_metadata (url):

    metadata = pd.read_json(url)

    var_dict = metadata['variables'].to_dict()
    variables = pd.DataFrame.from_dict(var_dict, orient='index').reset_index()
    variables.rename(columns={'index': 'var_code'}, inplace=True)
    return variables

def get_var_label(label_components):
    ''' Return variable's label by assembling user's inputs'''
    label = []
    for i in label_components:
        # Filter out empty elements
        if i != '':
            label.append(i.strip())

    if len(label) <= 1:  # A label should have at least 2 components
        var_label = None
    else:
        var_label = '!!'.join(label)  # Components are assembled and separated by "!!"

    return var_label

def get_var_id(data_year, acs_estimate, table_id, label_components):
    '''Call get_var_label function to retrieve variable label.
        Validate the format of table ID and variable label.
        If the table ID and variable label are valid, look up variable code based on table ID and variable label.'''

    b_var_url = f'https://api.census.gov/data/{data_year}/acs/acs{acs_estimate}/variables.json'
    s_var_url = f'https://api.census.gov/data/{data_year}/acs/acs{acs_estimate}/subject/variables.json'
    dp_var_url = f'https://api.census.gov/data/{data_year}/acs/acs{acs_estimate}/profile/variables.json'

    b_var = get_metadata(b_var_url)
    s_var = get_metadata(s_var_url)
    dp_var = get_metadata(dp_var_url)

    var_label = get_var_label(label_components)

    if not table_id or not table_id.lower().startswith(('b', 's', 'dp')) or var_label is None:
        raise ValueError('Invalid inputs!')

    # Assign target DataFrame based on table prefix
    result = pd.DataFrame()
    if table_id.lower().startswith('b'):
        result = b_var
    elif table_id.lower().startswith('s'):
        result = s_var
    elif table_id.lower().startswith('dp'):
        result = dp_var

    for component in label_components:
        if component.strip() != '':
            result = result.loc[(result['group'].str.contains(table_id, case=False, na=False))
                                & (result['label'].str.lower() == var_label.lower())]

    print(f'\nTable: {result["group"].values[0]}')
    print(f'Variable label: {result["label"].values[0]}')
    print(f'Variable code: {result["var_code"].values[0]}')


if __name__ == '__main__':
    try:
        year, estimate, table, components = input_prompt()
        get_var_id(year, estimate, table, components)
    except ValueError as excpt:
        print(excpt)
    except Exception as excpt:
        print(f'Variable not found! No matching table or label. ({excpt})')