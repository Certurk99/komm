import numpy as np

__all__ = ['ScalarQuantizer', 'UniformQuantizer']


class ScalarQuantizer:
    """
    General scalar quantizer. It is defined by a list of *levels*, :math:`v_0, v_1, \\ldots, v_{L-1}`, and a list of *thresholds*, :math:`t_0, t_1, \\ldots, t_L`, satisfying

    .. math::

       -\\infty = t_0 < v_0 < t_1 < v_1 < \\cdots < t_{L - 1} < v_{L - 1} < t_L = +\\infty.

    Given an input :math:`x \\in \\mathbb{R}`, the output of the quantizer is given by :math:`y = v_i` if and only if :math:`t_i \leq x < t_{i+1}`, where :math:`i \\in [0:L)`.
    """
    def __init__(self, levels, thresholds):
        """
        Constructor for the class. It expects the following parameters:

        :code:`levels` : 1D array of :obj:`float`
            The quantizer levels :math:`v_0, v_1, \\ldots, v_{L-1}`. It should be a list floats of length :math:`L`.

        :code:`thresholds` : 1D array of :obj:`float`
            The finite quantizer thresholds :math:`t_1, t_2, \\ldots, t_{L-1}`. It should be a list of floats of length :math:`L - 1`.

        Moreover, they must satisfy :math:`v_0 < t_1 < v_1 < \\cdots < t_{L - 1} < v_{L - 1}`.

        .. rubric:: Examples

        >>> quantizer = komm.ScalarQuantizer(levels=[-1.0, 0.0, 1.0], thresholds=[-0.5, 0.8])
        >>> x = np.linspace(-2.5, 2.5, num=11)
        >>> y = quantizer(x)
        >>> np.vstack([x, y])
        array([[-2.5, -2. , -1.5, -1. , -0.5,  0. ,  0.5,  1. ,  1.5,  2. ,  2.5],
               [-1. , -1. , -1. , -1. , -1. ,  0. ,  0. ,  1. ,  1. ,  1. ,  1. ]])
        """
        self._levels = np.array(levels, dtype=np.float)
        self._thresholds = np.array(thresholds, dtype=np.float)
        self._num_levels = self._levels.size

        if self._thresholds.size != self._num_levels - 1:
            raise ValueError("The length of 'thresholds' must be 'num_levels - 1'")

        interleaved = np.empty(2*self._num_levels - 1, dtype=np.float)
        interleaved[0::2] = self._levels
        interleaved[1::2] = self._thresholds

        if not np.array_equal(np.unique(interleaved), interleaved):
            raise ValueError("Invalid values for 'levels' and 'thresholds'")

    @property
    def levels(self):
        """
        The quantizer levels, :math:`v_0, v_1, \\ldots, v_{L-1}`.
        """
        return self._levels

    @property
    def thresholds(self):
        """
        The finite quantizer thresholds, :math:`t_1, t_2, \\ldots, t_{L-1}`.
        """
        return self._thresholds

    @property
    def num_levels(self):
        """
        The number of quantization levels, :math:`L`.
        """
        return self._num_levels

    def __call__(self, input_signal):
        input_signal_tile = np.tile(input_signal, reps=(self._thresholds.size, 1)).transpose()
        output_signal = self._levels[np.sum(input_signal_tile > self._thresholds, axis=1)]
        return output_signal

    def __repr__(self):
        args = 'levels={}, thresholds={}'.format(self._levels.tolist(), self._thresholds.tolist())
        return '{}({})'.format(self.__class__.__name__, args)


class UniformQuantizer(ScalarQuantizer):
    """
    Uniform scalar quantizer. It is a scalar quantizer (:obj:`ScalarQuantizer`) in which the separation between levels is constant, :math:`\\Delta`, and the thresholds are the mid-point between adjacent levels.
    """
    def __init__(self, num_levels, input_peak=1.0, type_='mid-riser'):
        """
        Constructor for the class. It expects the following parameters:

        :code:`num_levels` : :obj:`int`
            The number of quantization levels, :math:`L`.

        :code:`input_peak` : :obj:`float`, optional
            The peak of the input signal.

        .. rubric:: Examples

        >>> quantizer = komm.UniformQuantizer(num_levels=8)
        >>> quantizer.levels
        array([-1.  , -0.75, -0.5 , -0.25,  0.  ,  0.25,  0.5 ,  0.75])
        >>> quantizer.thresholds
        array([-0.875, -0.625, -0.375, -0.125,  0.125,  0.375,  0.625])
        >>> x = np.linspace(-0.5, 0.5, num=11)
        >>> y = quantizer(x)
        >>> np.vstack([x, y])  #doctest: +NORMALIZE_WHITESPACE
        array([[-0.5 , -0.4 , -0.3 , -0.2 , -0.1 ,  0.  ,  0.1 ,  0.2 ,  0.3 ,  0.4 ,  0.5 ],
               [-0.5 , -0.5 , -0.25, -0.25,  0.  ,  0.  ,  0.  ,  0.25,  0.25,  0.5 ,  0.5 ]])

        >>> quantizer = komm.UniformQuantizer(num_levels=4, input_peak=1.0, type_='unsigned')
        >>> quantizer.levels
        array([0.  , 0.25, 0.5 , 0.75])
        >>> quantizer.thresholds
        array([0.125, 0.375, 0.625])

        >>> quantizer = komm.UniformQuantizer(num_levels=4, input_peak=1.0, type_='mid-riser')
        >>> quantizer.levels
        array([-1. , -0.5,  0. ,  0.5])
        >>> quantizer.thresholds
        array([-0.75, -0.25,  0.25])

        >>> quantizer = komm.UniformQuantizer(num_levels=4, input_peak=1.0, type_='mid-tread')
        >>> quantizer.levels
        array([-0.75, -0.25,  0.25,  0.75])
        >>> quantizer.thresholds
        array([-0.5,  0. ,  0.5])
        """
        if type_ == 'unsigned':
            delta = input_peak / num_levels
            levels = input_peak * np.arange(num_levels) / num_levels
        elif type_ == 'mid-riser':
            delta = (2.0 * input_peak) / num_levels
            levels = input_peak * np.arange(-num_levels//2, num_levels//2) / (num_levels // 2)
        elif type_ == 'mid-tread':
            delta = (2.0 * input_peak) / num_levels
            levels = input_peak * np.arange(-num_levels//2, num_levels//2) / (num_levels // 2) + delta/2
        else:
            raise ValueError("Parameter 'type_' must be 'unsigned' or 'mid-riser' or 'mid-tread'")

        thresholds = (levels + delta/2)[:-1]
        super().__init__(levels, thresholds)

        self._quantization_step = delta
        self._input_peak = float(input_peak)
        self._type = type_

    @property
    def quantization_step(self):
        """
        The quantization step, :math:`\\Delta`.
        """
        return self._quantization_step

    @property
    def input_peak(self):
        """
        The peak of the input signal, :math:`m_\\mathrm{p}`.
        """
        return self._input_peak

    def __call__(self, input_signal):
        if self._type == 'unsigned':
            return 0
        elif self._type == 'mid-riser':
            return self._quantize_mid_riser(input_signal)
        elif self._type == 'mid-tread':
            return self._quantize_mid_tread(input_signal)

    def _quantize_mid_riser(self, input_signal):
        input_signal = np.array(input_signal, dtype=np.float)
        delta = self._quantization_step
        output_signal = delta * np.floor(input_signal / delta + 0.5)
        return output_signal

    def _quantize_mid_tread(self, input_signal):
        input_signal = np.array(input_signal, dtype=np.float)
        delta = self._quantization_step
        output_signal = delta * (np.floor(input_signal / delta) + 0.5)
        return output_signal

    def __repr__(self):
        args = "num_levels={}, input_peak={}, type_='{}'".format(self._num_levels, self._input_peak, self._type)
        return '{}({})'.format(self.__class__.__name__, args)
