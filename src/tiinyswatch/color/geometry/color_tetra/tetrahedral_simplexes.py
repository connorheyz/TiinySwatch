import numpy as np

class TetrahedralSimplexes:
    _simplexes = {
        4: np.array([
            [ 0.         ,  0.         ,  0.        ],
            [ 1.         ,  0.         ,  0.        ],
            [ 0.5        , -0.8660254  ,  0.        ],
            [ 0.5        , -0.28867513 ,  0.81649658],
        ]),
        5: np.array([
            [ 0.         ,  0.         ,  0.        ],
            [ 1.         ,  0.         ,  0.        ],
            [ 0.5        ,  0.57735027 ,  0.        ],
            [ 0.5        ,  0.4330127  ,  0.75      ],
            [ 0.5        , -0.28867513 ,  0.5       ],
        ]),
        6: np.array([
            [ 0.         ,  0.         ,  0.        ],
            [ 1.         ,  0.         ,  0.        ],
            [ 0.75       , -0.66143783 ,  0.        ],
            [ 0.5        ,  0.18898224 , -0.46291005],
            [ 0.5        , -0.18898224 ,  0.46291005],
            [ 0.25       , -0.47245559 , -0.46291005],
        ]),
        7: np.array([
            [ 0.         ,  0.         ,  0.        ],
            [ 1.         ,  0.         ,  0.        ],
            [ 0.5        ,  0.43130819 ,  0.        ],
            [ 0.78198662 , -0.08743618 , -0.61713194],
            [ 0.21801338 ,  0.25273503 , -0.56975602],
            [ 0.21801338 , -0.40105878 , -0.47712553],
            [ 0.5        , -0.41433308 ,  0.11981172],
        ]),
        8: np.array([
            [ 0.         ,  0.         ,  0.        ],
            [ 1.         ,  0.         ,  0.        ],
            [ 0.57820108 ,  0.47290832 ,  0.        ],
            [ 0.57820108 , -0.47004982 , -0.05191769],
            [ 0.74515445 ,  0.0318955  , -0.57930392],
            [ 0.20077831 , -0.28828535 , -0.52738623],
            [ 0.5        , -0.02140194 ,  0.38871399],
            [ 0.20077831 ,  0.34444129 , -0.49254937],
        ]),
        9: np.array([
            [ 0.00000000e+00,  0.00000000e+00,  0.00000000e+00],
            [ 1.00000000e+00,  0.00000000e+00,  0.00000000e+00],
            [ 7.72368257e-01, -5.84081760e-01,  0.00000000e+00],
            [ 1.96489032e-01, -5.42887383e-01,  2.44199250e-01],
            [ 7.72354113e-01,  2.18641551e-01,  5.41609140e-01],
            [ 4.99993740e-01, -1.41543148e-01, -3.50627251e-01],
            [ 4.99999598e-01,  3.78111184e-01, -1.87507175e-05],
            [ 1.96484613e-01, -2.32458838e-02,  5.94828131e-01],
            [ 6.96495116e-01, -4.01343183e-01,  5.94826015e-01],
        ]),
        10: np.array([
            [ 0.0        , 0.0         ,  0.0       ],
            [ 1.0        , 0.0         ,  0.0       ],
            [ 0.79970807 , -0.60038904 ,  0.0       ],
            [ 0.83974037 , -0.2850365  ,  0.46215826],
            [ 0.26528882 , -0.47943312 , -0.12002369],
            [ 0.49941013 ,  0.22427767 , -0.12218431],
            [ 0.38931385 , -0.61522583 ,  0.40989902],
            [ 0.2577637  , -0.07620869 ,  0.4923313 ],
            [ 0.67991329 , -0.22743668 , -0.40149184],
            [ 0.7010599  ,  0.25495123 ,  0.40034461],
        ]),
    }

    @staticmethod
    def get_simplex(n: int) -> np.ndarray:
        try:
            return TetrahedralSimplexes._simplexes[n].copy()
        except KeyError:
            raise KeyError(f"No simplex defined for n={n}")