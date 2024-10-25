import sys
import os
import ctypes

import numpy
from matplotlib import pyplot


class CSA:
    """
    Cubic spline approximation for re-gridding 2D data sets

    Parameters
    ----------
    xin : array-like
        an array of x data point locations
    yin : array-like
        an array of z data point locations
    zin : array-like
        an array of z data point locations
    sigma : array-like or None
        an array of errors for zin (standard deviation)
        None for no error (default)
    k : integer
        Set the spline sensitivity (default = 140).
        Reduce to get smoother results.
    nppc : integer
        Average number of points per cell (default = 5)
        Decrease to get smaller cells or increase to get larger cells
    npmin : integer
        Minimal number of points locally involved in spline
        calculation (default = 3)
    npmax : integer
        Maximum number of points locally involved in spline
        calculation (default = 40)

    Returns
    -------
    csa_interp : object
        This object can be called with arguments of x and y points to be
        interpolated to.  The input data, zin, can be reset by overwriting
        that object parameter.

    Examples
    --------

    .. plot ::
       :include-source:

        import numpy as np
        import matplotlib.pyplot as plt
        from pygridgen import csa
        xin = np.random.randn(10000)
        yin = np.random.randn(10000)
        zin = np.sin( xin**2 + yin**2 ) / (xin**2 + yin**2 )
        xout, yout = np.mgrid[-3:3:10j, -3:3:10j]
        csa_interp = csa.CSA(xin, yin, zin)
        zout = csa_interp(xout, yout)
        img = plt.imshow(zout)

    """

    _libcsa_paths = [
        ('libcsa.so', os.path.join(sys.prefix, 'lib')),
        ('libcsa', os.path.join(sys.prefix, 'lib')),
        ('libcsa.so', '/usr/local/lib'),
        ('libcsa', '/usr/local/lib'),
    ]

    for name, path in _libcsa_paths:
        try:
            _csa = numpy.ctypeslib.load_library(name, path)
            break
        except OSError:
            pass
        else:
            raise OSError('Failed to load the CSA library.')

    _csa.csa_approximatepoints2.restype = ctypes.POINTER(ctypes.c_double)

    def __init__(self, xin, yin, zin, sigma=None, npmin=3, npmax=40, k=140, nppc=5):
        self.xin = numpy.asarray(xin)
        self.yin = numpy.asarray(yin)

        if xin.size != yin.size:
            raise ValueError('xin and yin must have the same number '
                             'of elements')

        self._zin = zin

        self.sigma = sigma

        self.k = k
        self.nppc = nppc
        self.npmin = npmin
        self.npmax = npmax

    @property
    def zin(self):
        """ Input values to be approximated """
        return self._zin

    @zin.setter
    def zin(self, value):
        zin = numpy.asarray(value)
        if zin.size != self.xin.size:
            raise ValueError('zin must have the same number of elements as '
                             'xin and yin')
        self._zin = value

    def _calculate_points(self, xout, yout):
        xout = numpy.asarray(xout)
        yout = numpy.asarray(yout)

        nin = self.xin.size
        nout = xout.size

        if self.sigma is None:
            sigma = ctypes.POINTER(ctypes.c_double)()
        else:
            sigma = (ctypes.c_double * nin)(*(self.sigma * numpy.ones_like(self.xin)))

        zout = None

        zout = self._csa.csa_approximatepoints2(
            ctypes.c_int(nin),                         # int nin
            (ctypes.c_double * nin)(*self.xin.flat),   # double xin[]
            (ctypes.c_double * nin)(*self.yin.flat),   # double yin[]
            (ctypes.c_double * nin)(*self._zin.flat),  # double zin[]
            sigma,                                     # double sigma[] or NULL
            ctypes.c_int(nout),                        # int nout
            (ctypes.c_double * nout)(*xout.flat),      # double xout[]
            (ctypes.c_double * nout)(*yout.flat),      # double yout[]
            ctypes.c_int(self.npmin),                  # int npmin
            ctypes.c_int(self.npmax),                  # int npmax
            ctypes.c_int(self.k),                      # int k
            ctypes.c_int(self.nppc)                    # int nppc
        )

        zout = numpy.asarray([zout[i] for i in range(nout)])
        zout.shape = xout.shape
        return numpy.ma.masked_where(numpy.isnan(zout), zout)

    def __call__(self, xout, yout):
        """
        Return interpolated values of ``zin``

        Parameters
        ----------
        xout, yout : array-like
            Two-dimensional arrays of x/y coordinates at which ``zout``
            should be estimated.

        Returns
        -------
        zout : numpy ndarray
            Interpolated z-values.

        """

        xout = numpy.asarray(xout)
        yout = numpy.asarray(yout)
        return self._calculate_points(xout, yout)

    def plot(self, xout, yout, ax=None, mesh_opts=None, scatter_opts=None):
        """
        Plot the input and output data set from the cubic split
        approximation.

        Parameters
        ----------
        xout, yout : array-like
            Two-dimensional arrays of x/y coordinates at which ``zout``
            should be estimated.
        ax : matplotlib Axes, optional
            The axes on which the plot should be drawn. If not provided,
            a new axes and figure will be created.
        mesh_opts, scatter_opts : dict, optional
            Dictionary of plotting options passed to matplotlib's
            `pcolormesh` and `scatter` functions, respectively.

        Returns
        -------
        ax : matplotlib Axes.

        """

        if ax is None:
            fig, ax = pyplot.subplots()
        else:
            fig = ax.figure

        if mesh_opts is None:
            mesh_opts = {}

        if scatter_opts is None:
            scatter_opts = {}

        zout = self._calculate_points(xout, yout)
        mesh = ax.pcolormesh(xout, yout, zout, **mesh_opts)
        dots = ax.scatter(self.xin, self.yin, 10, self.zin, **scatter_opts)
        cbar = fig.colorbar(mesh, ax=ax)
        return fig, {'surface': mesh, 'points': dots, 'colorbar': cbar}
