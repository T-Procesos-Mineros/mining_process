def read_text_data(file_path):
    """
    Read a text file with comma-separated values and return a list of lists with the data.
    
    Args:
        file_path (str): Path of the text file.
    
    Returns:
        list: List of lists with the data from the text file.
    """
    data = []
    with open(file_path, 'r') as file:
        for line in file:
            row = line.strip().split(',')
            data.append(row)
    return data


# # Example of how to use the read_text_data function

# # Path to your text file in scenarios folder
# text_file = "src\data\Scenarios\Scenario00.txt"

# # Read data from the text file
# data = read_text_data(text_file)

# # Print the data
# for row in data:
#     print(row)
