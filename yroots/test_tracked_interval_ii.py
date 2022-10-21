import pytest
import yroots.ChebyshevSubdivisionSolver as chebsolver
import numpy as np

n = 5
interval = np.array([np.random.random(n)*-1,np.random.random(n)]).T
tracked = chebsolver.TrackedInterval(interval)

def test_size_tracked():
    assert tracked.size() == np.product(interval[:,1] - interval[:,0])

def test_copy():
    tracked_copy = tracked.copy()
    assert np.allclose(tracked.interval,tracked_copy.interval) == True
    for i in range(len(tracked.transforms)):
        assert np.allclose(tracked.transforms[i],tracked_copy.transforms[i])
    assert np.allclose(tracked.topInterval, tracked_copy.topInterval) == True
    assert tracked.empty == tracked_copy.empty
    assert tracked.ndim == tracked_copy.ndim

def test_contains():
    point_bad = 5*np.random.random(n)
    in_bool_bad = np.all(point_bad >= tracked.interval[:,0]) and np.all(point_bad <= tracked.interval[:,1])
    assert in_bool_bad == tracked.__contains__(point_bad)
    point_good = np.zeros(n)
    in_bool_good = np.all(point_good >= tracked.interval[:,0]) and np.all(point_good <= tracked.interval[:,1])
    assert in_bool_good == tracked.__contains__(point_good)

def test_overlaps():
    test_interval = np.array([np.array([-1]*n),np.array([1]*n)])
    test_object = chebsolver.TrackedInterval(test_interval)
    bad_interval = np.array([np.array([2]*n),np.array([3]*n)]).T
    good_interval = np.array([np.array([0.2]*n),np.array([0.3]*n)]).T
    assert test_object.overlapsWith(bad_interval) == False
    assert test_object.overlapsWith(good_interval) == True

def test_linearCheck1():
    A = np.array([[0.12122536, 0.58538202, 0.28835862, 0.90334211, 0.17009259],
       [0.8381725 , 0.49698512, 0.1761786 , 0.40609808, 0.30879373],
       [0.73555404, 0.27864861, 0.54397928, 0.90567404, 0.49692915],
       [0.80468046, 0.41315412, 0.99003273, 0.98359542, 0.25886889],
       [0.43675962, 0.13999244, 0.9270024 , 0.17952587, 0.79644536]])
    totalErrs = np.array([0.674356  , 0.36258152, 0.47688965, 0.58847478, 0.37490811])
    consts = np.array([0.8383123 , 0.44548865, 0.55498803, 0.91740163, 0.0369741 ])
    result = chebsolver.linearCheck1(totalErrs,A,consts)
    assert np.allclose(result[0],np.array([0.5674142 , 0.27043788, 0.59556943, 0.47344229, 0.52927329])) == True
    assert np.allclose(result[1],np.array([-9.26781277, -4.01661874, -4.47577129, -2.30115309, -6.89248849])) == True
    