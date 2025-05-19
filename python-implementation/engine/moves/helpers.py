# File to helper functions


# Function used to check bounds
# Will be used for everything, making it a function early
# f = file, r = rank
def check_bounds(f, r):
    return 1 <= f <= 8 and 1 <= r <= 8
