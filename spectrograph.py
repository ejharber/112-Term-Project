#!/usr/bin/env python
import sys
import numpy as np
import wave
import math
from scipy.signal import lfilter, hamming
from scipy.fftpack import fft, ifft

# audio analisis taken off of scikits talbox package
#from scikits.talkbox.linpred._lpc import levinson as c_levinson

def c_levinson(r, order):
    """Levinson-Durbin recursion, to efficiently solve symmetric linear systems
    with toeplitz structure.

    Parameters
    ---------
    r : array-like
        input array to invert (since the matrix is symmetric Toeplitz, the
        corresponding pxp matrix is defined by p items only). Generally the
        autocorrelation of the signal for linear prediction coefficients
        estimation. The first item must be a non zero real.

    Notes
    ----
    This implementation is in python, hence unsuitable for any serious
    computation. Use it as educational and reference purpose only.

    Levinson is a well-known algorithm to solve the Hermitian toeplitz
    equation:

                       _          _
        -R[1] = R[0]   R[1]   ... R[p-1]    a[1]
         :      :      :          :      *  :
         :      :      :          _      *  :
        -R[p] = R[p-1] R[p-2] ... R[0]      a[p]
                       _
    with respect to a (  is the complex conjugate). Using the special symmetry
    in the matrix, the inversion can be done in O(p^2) instead of O(p^3).
    """
    r = np.atleast_1d(r)
    if r.ndim > 1:
        raise ValueError("Only rank 1 are supported for now.")

    n = r.size
    if n < 1:
        raise ValueError("Cannot operate on empty array !")
    elif order > n - 1:
        raise ValueError("Order should be <= size-1")

    if not np.isreal(r[0]):
        raise ValueError("First item of input must be real.")
    elif not np.isfinite(1/r[0]):
        raise ValueError("First item should be != 0")

    # Estimated coefficients
    a = np.empty(int(order+1), r.dtype)
    # temporary array
    t = np.empty(int(order+1), r.dtype)
    # Reflection coefficients
    k = np.empty(int(order), r.dtype)

    a[0] = 1.
    e = r[0]

    for i in range(1, int(order+1)):
        acc = r[i]
        for j in range(1, i):
            acc += a[j] * r[i-j]
        k[i-1] = -acc / e
        a[i] = k[i-1]

        for j in range(int(order)):
            t[j] = a[j]

        for j in range(1, i):
            a[j] += k[i-1] * np.conj(t[i-j])

        e *= 1 - k[i-1] * np.conj(k[i-1])

    return a, e, k

"""
Estimate formants using LPC.
"""

def nextpow2(n):
    """Return the next power of 2 such as 2^p >= n.

    Notes
    -----

    Infinite and nan are left untouched, negative values are not allowed."""
    if np.any(n < 0):
        raise ValueError("n should be > 0")

    if np.isscalar(n):
        f, p = np.frexp(n)
        if f == 0.5:
            return p-1
        elif np.isfinite(f):
            return p
        else:
            return f
    else:
        f, p = np.frexp(n)
        res = f
        bet = np.isfinite(f)
        exa = (f == 0.5)
        res[bet] = p[bet]
        res[exa] = p[exa] - 1
        return res

def _acorr_last_axis(x, nfft, maxlag, onesided=False, scale='none'):
    a = np.real(ifft(np.abs(fft(x, n=nfft) ** 2)))
    if onesided:
        b = a[..., :maxlag]
    else:
        b = np.concatenate([a[..., nfft-maxlag+1:nfft],
                            a[..., :maxlag]], axis=-1)
    #print b, a[..., 0][..., np.newaxis], b / a[..., 0][..., np.newaxis]
    if scale == 'coeff':
        return b / a[..., 0][..., np.newaxis]
    else:
        return b

def acorr(x, axis=-1, onesided=False, scale='none'):
    """Compute autocorrelation of x along given axis.

    Parameters
    ----------
        x : array-like
            signal to correlate.
        axis : int
            axis along which autocorrelation is computed.
        onesided: bool, optional
            if True, only returns the right side of the autocorrelation.
        scale: {'none', 'coeff'}
            scaling mode. If 'coeff', the correlation is normalized such as the
            0-lag is equal to 1.

    Notes
    -----
        Use fft for computation: is more efficient than direct computation for
        relatively large n.
    """
    if not np.isrealobj(x):
        raise ValueError("Complex input not supported yet")
    if not scale in ['none', 'coeff']:
        raise ValueError("scale mode %s not understood" % scale)

    maxlag = x.shape[axis]
    nfft = 2 ** nextpow2(2 * maxlag - 1)

    if axis != -1:
        x = np.swapaxes(x, -1, axis)
    a = _acorr_last_axis(x, nfft, maxlag, onesided, scale)
    if axis != -1:
        a = np.swapaxes(a, -1, axis)
    return a

def lpc(signal, order, axis=-1):
    """Compute the Linear Prediction Coefficients.

    Return the order + 1 LPC coefficients for the signal. c = lpc(x, k) will
    find the k+1 coefficients of a k order linear filter:

      xp[n] = -c[1] * x[n-2] - ... - c[k-1] * x[n-k-1]

    Such as the sum of the squared-error e[i] = xp[i] - x[i] is minimized.

    Parameters
    ----------
    signal: array_like
        input signal
    order : int
        LPC order (the output will have order + 1 items)

    Returns
    -------
    a : array-like
        the solution of the inversion.
    e : array-like
        the prediction error.
    k : array-like
        reflection coefficients.

    Notes
    -----
    This uses Levinson-Durbin recursion for the autocorrelation matrix
    inversion, and fft for the autocorrelation computation.

    For small order, particularly if order << signal size, direct computation
    of the autocorrelation is faster: use levinson and correlate in this case."""
    n = signal.shape[axis]
    if order > n:
        raise ValueError("Input signal must have length >= order")

    r = acorr_lpc(signal, axis)
    return levinson(r, order, axis)

def _acorr_last_axis(x, nfft, maxlag):
    a = np.real(ifft(np.abs(fft(x, n=nfft) ** 2)))
    return a[..., :maxlag+1] / x.shape[-1]

def acorr_lpc(x, axis=-1):
    """Compute autocorrelation of x along the given axis.

    This compute the biased autocorrelation estimator (divided by the size of
    input signal)

    Notes
    -----
        The reason why we do not use acorr directly is for speed issue."""
    if not np.isrealobj(x):
        raise ValueError("Complex input not supported yet")

    maxlag = x.shape[axis]
    nfft = 2 ** nextpow2(2 * maxlag - 1)

    if axis != -1:
        x = np.swapaxes(x, -1, axis)
    a = _acorr_last_axis(x, nfft, maxlag)
    if axis != -1:
        a = np.swapaxes(a, -1, axis)
    return a

def levinson(r, order, axis = -1):
    """Levinson-Durbin recursion, to efficiently solve symmetric linear systems
    with toeplitz structure.

    Parameters
    ----------
    r : array-like
        input array to invert (since the matrix is symmetric Toeplitz, the
        corresponding pxp matrix is defined by p items only). Generally the
        autocorrelation of the signal for linear prediction coefficients
        estimation. The first item must be a non zero real, and corresponds
        to the autocorelation at lag 0 for linear prediction.
    order : int
        order of the recursion. For order p, you will get p+1 coefficients.
    axis : int, optional
        axis over which the algorithm is applied. -1 by default.

    Returns
    -------
    a : array-like
        the solution of the inversion (see notes).
    e : array-like
        the prediction error.
    k : array-like
        reflection coefficients.

    Notes
    -----
    Levinson is a well-known algorithm to solve the Hermitian toeplitz
    equation: ::

                       _          _
        -R[1] = R[0]   R[1]   ... R[p-1]    a[1]
         :      :      :          :         :
         :      :      :          _      *  :
        -R[p] = R[p-1] R[p-2] ... R[0]      a[p]

    with respect to a. Using the special symmetry in the matrix, the inversion
    can be done in O(p^2) instead of O(p^3).

    Only double argument are supported: float and long double are internally
    converted to double, and complex input are not supported at all.
    """
    if axis != -1:
        r = np.swapaxes(r, axis, -1)
    a, e, k = c_levinson(r, order)
    if axis != -1:
        a = np.swapaxes(a, axis, -1)
        e = np.swapaxes(e, axis, -1)
        k = np.swapaxes(k, axis, -1)
    return a, e, k

def get_formants(file_path):
    # code based on matlab code for formant comparison 
    # gets formant values in a list
    if(type(file_path) == str):
        # Read from file.
        spf = wave.open(file_path, 'r')
        x = spf.readframes(-1)

    else:
        spf = file_path[0]
        for i in range(1, len(file_path)):
            spf += file_path[i]

        x = spf


    # Get file as numpy array.

    x = np.fromstring(x, 'Int16')

    # Get Hamming window.
    N = len(x)
    w = np.hamming(N)

    # Apply window and high pass filter.
    x1 = x * w
    x1 = lfilter([1], [1., 0.63], x1)
    # Get LPC.

    Fs = 44100 #spf.getframerate()
    ncoeff = 2 + Fs / 1000
    A, e, k = lpc(x1, ncoeff)


    # Get roots.
    rts = np.roots(A)
    rts = [r for r in rts if np.imag(r) >= 0]

    # Get angles.
    angz = np.arctan2(np.imag(rts), np.real(rts))

    # Get frequencies.
    #Fs = spf.getframerate()
    frqs = sorted(angz * (Fs / (2 * math.pi)))

    return frqs



