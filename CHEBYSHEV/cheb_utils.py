# A collection of functions used in the F4 Macaulay and TVB solvers
import numpy as np
import itertools
from scipy.linalg import qr, solve_triangular
from scipy.misc import comb

class InstabilityWarning(Warning):
    pass

class TVBError(RuntimeError):
    pass

class Term(object):
    '''
    Terms are just tuples of exponents with the grevlex ordering
    '''
    def __init__(self,val):
        self.val = tuple(val)

    def __repr__(self):
        return str(self.val) + ' with grevlex order'

    def __lt__(self, other, order = 'grevlex'):
        '''
        Redfine less-than according to grevlex
        '''
        if order == 'grevlex': #Graded Reverse Lexographical Order
            if sum(self.val) < sum(other.val):
                return True
            elif sum(self.val) > sum(other.val):
                return False
            else:
                for i,j in zip(reversed(self.val),reversed(other.val)):
                    if i < j:
                        return False
                    if i > j:
                        return True
                return False
        elif order == 'lexographic': #Lexographical Order
            for i,j in zip(self.val,other.val):
                if i < j:
                    return True
                if i > j:
                    return False
            return False
        elif order == 'grlex': #Graded Lexographical Order
            if sum(self.val) < sum(other.val):
                return True
            elif sum(self.val) > sum(other.val):
                return False
            else:
                for i,j in zip(self.val,other.val):
                    if i < j:
                        return True
                    if i > j:
                        return False
                return False

def divides(mon1, mon2):
    '''
    parameters
    ----------
    mon1 : tuple
        contains the exponents of the monomial divisor
    mon2 : tuple
        contains the exponents of the monomial dividend

    returns
    -------
    boolean
        true if mon1 divides mon2, false otherwise
    '''
    return np.all(np.subtract(mon2, mon1) >= 0)

def row_swap_matrix(matrix):
    '''Rearrange the rows of matrix so it is close to upper traingular.

    Parameters
    ----------
    matrix : 2D numpy array
        The matrix whose rows need to be switched

    Returns
    -------
    2D numpy array
        The same matrix but with the rows changed so it is close to upper
        triangular

    Examples
    --------
    >>> utils.row_swap_matrix(np.array([[0,2,0,2],[0,1,3,0],[1,2,3,4]]))
    array([[1, 2, 3, 4],
           [0, 2, 0, 2],
           [0, 1, 3, 0]])
    '''
    leading_mon_columns = list()
    for row in matrix:
        leading_mon_columns.append(np.where(row!=0)[0][0])

    return matrix[np.argsort(leading_mon_columns)]

def clean_zeros_from_matrix(array, accuracy=1.e-10):
    '''Sets all values in the array less than the given accuracy to 0.

    Parameters
    ----------
    array : numpy array
    accuracy : float, optional
        Values in the matrix less than this will be set to 0.

    Returns
    -------
    array : numpy array
        Same array, but with values less than the given accuracy set to 0.
    '''
    array[(array < accuracy) & (array > -accuracy)] = 0
    return array

def slice_top(matrix):
    ''' Gets the n-d slices needed to slice a matrix into the top corner of another.

    Parameters
    ----------
    coeff : numpy matrix.
        The matrix of interest.
    Returns
    -------
    slices : list
        Each value of the list is a slice of the matrix in some dimension. It is exactly the size of the matrix.
    '''
    slices = list()
    for i in matrix.shape:
        slices.append(slice(0,i))
    return slices

def slice_bottom(matrix):
    ''' Gets the n-d slices needed to slice a matrix into the bottom corner of another.

    Parameters
    ----------
    coeff : numpy matrix.
        The matrix of interest.
    Returns
    -------
    slices : list
        Each value of the list is a slice of the matrix in some dimension. It is exactly the size of the matrix.
    '''
    slices = list()
    for i in matrix.shape:
        slices.append(slice(-i,None))
    return slices

def match_poly_dimensions(polys):
    '''Matches the dimensions of a list of polynomials.

    Parameters
    ----------
    polys : list
        Polynomials of possibly different dimensions.

    Returns
    -------
    new_polys : list
        The same polynomials but of the same dimensions.
    '''
    dim = max(poly.dim for poly in polys)
    new_polys = list()
    for poly in polys:
        if poly.dim != dim:
            coeff_shape = list(poly.shape)
            for i in range(dim - poly.dim):
                coeff_shape.insert(0,1)
            poly.__init__(poly.coeff.reshape(coeff_shape))
        new_polys.append(poly)
    return new_polys

def match_size(a,b):
    '''
    Matches the shape of two matrixes.

    Parameters
    ----------
    a, b : ndarray
        Matrixes whose size is to be matched.

    Returns
    -------
    a, b : ndarray
        Matrixes of equal size.
    '''
    new_shape = np.maximum(a.shape, b.shape)

    a_new = np.zeros(new_shape)
    a_new[slice_top(a)] = a
    b_new = np.zeros(new_shape)
    b_new[slice_top(b)] = b
    return a_new, b_new

def get_var_list(dim):
    '''Returns a list of the variables [x_1, x_2, ..., x_n] as tuples.'''
    _vars = []
    var = [0]*dim
    for i in range(dim):
        var[i] = 1
        _vars.append(tuple(var))
        var[i] = 0
    return _vars

def mon_combosHighest(mon, numLeft, spot = 0):
    '''Finds all the monomials of a given degree and returns them. Works recursively.

    Very similar to mon_combos, but only returns the monomials of the desired degree.

    Parameters
    --------
    mon: list
        A list of zeros, the length of which is the dimension of the desired monomials. Will change
        as the function searches recursively.
    numLeft : int
        The degree of the monomials desired. Will decrease as the function searches recursively.
    spot : int
        The current position in the list the function is iterating through. Defaults to 0, but increases
        in each step of the recursion.

    Returns
    -----------
    answers : list
        A list of all the monomials.
    '''
    answers = list()
    if len(mon) == spot+1: #We are at the end of mon, no more recursion.
        mon[spot] = numLeft
        answers.append(mon.copy())
        return answers
    if numLeft == 0: #Nothing else can be added.
        answers.append(mon.copy())
        return answers
    temp = mon.copy() #Quicker than copying every time inside the loop.
    for i in range(numLeft+1): #Recursively add to mon further down.
        temp[spot] = i
        answers += mon_combosHighest(temp, numLeft-i, spot+1)
    return answers

def mon_combos(mon, numLeft, spot = 0):
    '''Finds all the monomials up to a given degree and returns them. Works recursively.

    Parameters
    --------
    mon: list
        A list of zeros, the length of which is the dimension of the desired monomials. Will change
        as the function searches recursively.
    numLeft : int
        The degree of the monomials desired. Will decrease as the function searches recursively.
    spot : int
        The current position in the list the function is iterating through. Defaults to 0, but increases
        in each step of the recursion.

    Returns
    -----------
    answers : list
        A list of all the monomials.
    '''
    answers = list()
    if len(mon) == spot+1: #We are at the end of mon, no more recursion.
        for i in range(numLeft+1):
            mon[spot] = i
            answers.append(mon.copy())
        return answers
    if numLeft == 0: #Nothing else can be added.
        answers.append(mon.copy())
        return answers
    temp = mon.copy() #Quicker than copying every time inside the loop.
    for i in range(numLeft+1): #Recursively add to mon further down.
        temp[spot] = i
        answers += mon_combos(temp, numLeft-i, spot+1)
    return answers

def inverse_P(P):
    '''The inverse of P, the array with column switching indexes.

    Parameters
    ----------
    P : array-like
        1D array P returned by scipy's QRP decomposition.

    Returns
    -------
    1D numpy array
        The indexes needed to switch the columns back to their original
        positions.

    See Also
    --------
    scipy.linalg.qr : QR decomposition (with pivoting=True).

    '''
    inverse = np.empty_like(P)
    inverse[P] = np.arange(len(P))
    return inverse

def sort_polys_by_degree(polys, ascending = True):
    '''Sorts the polynomials by their degree.

    Parameters
    ----------
    polys : list.
        A list of polynomials.
    ascending : bool
        Defaults to True. If True the polynomials are sorted in order of ascending degree. If False they
        are sorted in order of descending degree.
    Returns
    -------
    sorted_polys : list
        A list of the same polynomials, now sorted.
    '''
    degs = [poly.degree for poly in polys]
    argsort_list = np.argsort(degs)
    sorted_polys = list()
    for i in argsort_list:
        sorted_polys.append(polys[i])
    if ascending:
        return sorted_polys
    else:
        return sorted_polys[::-1]

def deg_d_polys(polys, deg, dim):
    '''Finds the rows of the Macaulay Matrix of degree deg.

    Iterating through this for each needed degree creates a full rank matrix in all dimensions,
    getting rid of the extra rows that are there when we do all the monomial multiplications.

    The idea behind this algorithm comes from that cool triangle thing I drew on a board once, I have
    no proof of it, but it seems to work real good.

    It is also less stable than the other version.

    Parameters
    ----------
    polys : list.
        A list of polynomials.
    deg: int
        The desired degree.
    dim: int
        The dimension of the polynomials.
    Returns
    -------
    poly_coeff_list : list
        A list of the polynomials of degree deg to be added to the Macaulay Matrix.
    '''
    ignoreVar = 0
    poly_coeff_list = list()
    for poly in polys:
        mons = mon_combosHighest([0]*dim,deg - poly.degree)
        for mon in mons:
            if np.all([mon[i] <= (polys[i].degree - 1) for i in range(ignoreVar)]):
                poly_coeff_list.append(poly.mon_mult(mon, returnType = 'Matrix'))
        ignoreVar += 1
    return poly_coeff_list

def num_mons(deg, dim):
    '''Returns the number of monomials of a certain degree and dimension.

    Parameters
    ----------
    deg : int.
        The degree desired.
    dim : int
        The dimension desired.
    Returns
    -------
    num_mons : int
        The number of monomials of the given degree and dimension.
    '''
    return comb(deg+dim-1,deg,exact=True)

def deg_d_polys(polys, deg, dim):
    '''Finds the rows of the Macaulay Matrix of degree deg.

    Iterating through this for each needed degree creates a full rank matrix in all dimensions,
    getting rid of the extra rows that are there when we do all the monomial multiplications.

    The idea behind this algorithm comes from that cool triangle thing I drew on a board once, I have
    no proof of it, but it seems to work real good.

    It is also less stable than the other version.

    Parameters
    ----------
    polys : list.
        A list of polynomials.
    deg: int
        The desired degree.
    dim: int
        The dimension of the polynomials.
    Returns
    -------
    poly_coeff_list : list
        A list of the polynomials of degree deg to be added to the Macaulay Matrix.
    '''
    ignoreVar = 0
    poly_coeff_list = list()
    for poly in polys:
        mons = mon_combosHighest([0]*dim,deg - poly.degree)
        for mon in mons:
            if np.all([mon[i] <= (polys[i].degree - 1) for i in range(ignoreVar)]):
                poly_coeff_list.append(poly.mon_mult(mon, returnType = 'Matrix'))
        ignoreVar += 1
    return poly_coeff_list

def arrays(deg,dim,mon):
    '''Finds a part of the permutation array.

    Parameters
    ----------
    deg : int.
        The degree of the Macaulay matrix that the row is in.
    dim: int
        The dimension of the polynomials in the Macaualy matrix that the row is in.
    mon: int
        The monomial we are multiplying by.
        0 -> multiplying by x0
        1 -> multiplying by x1
        ...
        n -> multiplying by xn
    Returns
    -------
    arrays : numpy array
        The array is full of True/False values, using np.where the array is True will generate the permutation array.
    '''
    if dim-1==mon:
        total = num_mons(deg, dim)
        end = num_mons(deg, dim-1)
        return [True]*(total-end)+[False]*end
    elif deg==1:
        temp = [False]*(dim)
        temp[dim-mon-1] = True
        return temp
    else:
        return arrays(deg-1,dim,mon)+arrays(deg,dim-1,mon)

def permutation_array(deg,dim,mon):
    '''Finds the permutation array to multiply a row of a matrix by a certain monomial.

    Parameters
    ----------
    deg : int.
        The degree of the Macaulay matrix that the row is in.
    dim: int
        The dimension of the polynomials in the Macaualy matrix that the row is in.
    mon: int
        The monomial we are multiplying by.
        0 -> multiplying by x0
        1 -> multiplying by x1
        ...
        n -> multiplying by xn
    Returns
    -------
    permutation_array : numpy array
        Permutting a row in the Macaulay matrix by this array will be equivalent to multiplying by mon.
    '''
    if mon == dim -1:
        array = [False]
        for d in range(1,deg+1):
            array = arrays(d,dim,mon) + array
    else:
        array = [False]
        first = [False]*(dim)
        first[dim-mon-1] = True
        array = first + array
        for d in range(2,deg+1):
            first = first + arrays(d,dim-1,mon)
            array = first+array
    return np.array(inverse_P(np.hstack((np.where(~np.array(array))[0],np.where(array)[0]))))

def all_permutations(deg, dim, matrixDegree, permutations = None, current_degree = 2):
    '''Finds all the permutation arrays needed to create a Macaulay Matrix.

    Parameters
    ----------
    deg: int
        Permutation arrays will be computed for all monomials up to this degree.
    dim: int
        The dimension the monomials for which permutation degrees.
    matrixDegree: int
        The degree of the Macaulay Matrix that will be created. This is needed to get the length of the rows.
    permutations: dict
        Defaults to none. The permutations that have already been computed.
    current_degree: int
        Defaults to 2. The degree of permutations that have already been computed.
    Returns
    -------
    permutations : dict
        The keys of the dictionary are tuple representation of the monomials, and each value is
        the permutation array corresponding to multiplying by that monomial.
    '''
    if permutations is None:
        permutations = {}
        permutations[tuple([0]*dim)] = np.arange(np.sum([num_mons(deg,dim) for deg in range(matrixDegree+1)]))
        for i in range(dim):
            mon = [0]*dim
            mon[i] = 1
            mon = tuple(mon)
            permutations[mon] = permutation_array(matrixDegree,dim,dim-1-i)

    varList = get_var_list(dim)

    for d in range(current_degree,deg+1):
        mons = mon_combosHighest([0]*dim,d)
        for mon in mons:
            for var in varList:
                diff = tuple(np.subtract(mon,var))
                if diff in permutations:
                    permutations[tuple(mon)] = permutations[var][permutations[diff]]
                    break
    return permutations

def mons_ordered(dim, deg):
    mons_ordered = []
    for i in range(deg+1):
        for j in mon_combosHighest([0]*dim,i):
            mons_ordered.append(j)
    return np.array(mons_ordered)

def cheb_perturbation3(mult_mon, mons, mon_dict, var):
    """
    Calculates the Cheb perturbation for the case where mon is greater than poly_mon

    Parameters
    ----------
    mult_mon : tuple
        the monomial that multiplies the polynomial
    mons : array
        Array of monomials in the polynomial
    mon_dict : dict
        Dictionary of the index of each monomial.
    var : int
        index of the variable that is being calculated

    Returns
    --------
    cheb_pertubation3 : list
        list of indexes for the 3rd case of cheb mon mult

    """
    perturb = [0]*len(mon_dict)
    #print(mons)
    mons_needed = mons[np.where(mons[:,var] < mult_mon[var])]
    #print(mult_mon)
    #print(mons_needed)
    for monomial in mons_needed:
        idx = mon_dict[tuple(monomial)]
        diff = tuple(np.abs(np.subtract(monomial,mult_mon)))
        try:
            idx2 = mon_dict[diff]
            perturb[idx2] = idx
        except KeyError as k:
            pass

    return perturb

def cheb_perturbation2(mult_mon, mons, mon_dict, var):
    """
    Calculates the Cheb perturbation for the case where mon is greater than poly_mon

    Parameters
    ----------
    mult_mon : tuple
        the monomial that multiplies the polynomial
    mons : array
        Array of monomials in the polynomial
    mon_dict : dict
        Dictionary of the index of each monomial.
    var : int
        index of the variable that is being calculated

    Returns
    --------
    cheb_pertubation3 : list
        list of indexes for the 3rd case of cheb mon mult

    """
    perturb = [int(0)]*len(mon_dict)
    mons_needed = mons[np.where(mons[:,var] >= mult_mon[var])]
    for monomial in mons_needed:
        idx = mon_dict[tuple(monomial)]
        diff = tuple(np.abs(np.subtract(monomial,mult_mon)))
        try:
            idx2 = mon_dict[diff]
            perturb[idx2] = idx
        except KeyError as k:
            pass

        #print()
        #print(mon_dict)
        #print(perturb)
    return perturb

def all_permutations_cheb(deg,dim,matrixDegree, current_degree = 2):
    '''Finds all the permutation arrays needed to create a Macaulay Matrix for Chebyshev Basis.

    Parameters
    ----------
    deg: int
        Permutation arrays will be computed for all monomials up to this degree.
    dim: int
        The dimension the monomials for which permutation degrees.
    matrixDegree: int
        The degree of the Macaulay Matrix that will be created. This is needed to get the length of the rows.
    current_degree: int
        Defaults to 2. The degree of permutations that have already been computed.
    Returns
    -------
    permutations : dict
        The keys of the dictionary are tuple representation of the monomials, and each value is
        the permutation array corresponding to multiplying by that monomial.
    '''
    permutations = {}
    mons = mons_ordered(dim,matrixDegree)
    #print(mons)
    mon_dict = {}
    for i,j in zip(mons[::-1], range(len(mons))):
        mon_dict[tuple(i)] = j
    for i in range(dim):
        mon = [0]*dim
        mon[i] = 1
        mon = tuple(mon)
        num_in_top = num_mons(matrixDegree, dim) + num_mons(matrixDegree-1, dim)
        P = permutation_array(matrixDegree,dim,dim-1-i)
        P_inv = inverse_P(P)
        A = np.where(mons[:,i] == 1)
        P2 = np.zeros_like(P)
        P2[::-1][A] = P[::-1][A]
        P_inv[:num_in_top] = np.zeros(num_in_top)
        permutations[mon] = np.array([P, P_inv, P2])
    mons2 = mons_ordered(dim,matrixDegree-1)
    for i in range(dim):
        mons = mons_1D(dim, deg, i)
        mon = [0]*dim
        mon[i] = 1
        #print(mons)
        for calc in mons:
            diff = tuple(np.subtract(calc, mon))
            if diff in permutations:
                mon = tuple(mon)
                #print(num_mons(matrixDegree, dim))
                #print(calc, calc[i])
                #print(num_mons(matrixDegree-calc[i], dim))
                num_in_top = num_mons(matrixDegree, dim) + num_mons(matrixDegree-calc[i]+2, dim)
                P = permutations[mon][0][permutations[diff][0]]
                #ptest = cheb_perturbation1(calc, mons2, mon_dict, i)
                #print(P, '\n', ptest, '\n')
                #P_inv = inverse_P(P)
                #P_inv[:num_in_top] = int(0)
                P_inv = cheb_perturbation2(calc, mons2, mon_dict, i)
                #P_inv[:num_in_top] = np.zeros(num_in_top)
                P2 = cheb_perturbation3(calc, mons2, mon_dict, i)
                #print(P_inv)
                #print(calc, " : " , P2)
                permutations[tuple(calc)] = np.array([P, P_inv, P2])
    #print(permutations)

    return permutations

def mons_1D(dim, deg, var):
    """
    Finds the monomials of one variable up to a given degree.

    Parameters
    ---------
    dim: int
        Dimension of the monomial
    deg : int
        Desired degree of highest monomial returned
    var : int
        index of the variable of desired monomials

    Returns
    --------
    mons_1D : ndarray
        Array of monomials where each row is a monomial.

    """
    mons = []
    for i in range(2, deg+1):
        mon = [0]*dim
        mon[var] = i
        mons.append(mon)
    return np.array(mons)
