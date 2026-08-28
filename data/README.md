# Dataset

68 Discrete Dislocation Dynamics runs generated with OpenDiS, spanning two
loading modes, four target stresses, three loading rates and three initial
dislocation densities.

## Layout

```
raw/         one CSV per DDD run, as written by the OpenDiS driver
resampled/   the same runs on the common 1000-point uniform time grid
```

## File naming

```
<mode>_<target stress>Mpa_<loading rate>_<initial density>.csv

shear_30Mpa_4e13_1.43e12.csv
uniaxial_50Mpa_8e13_2.055e12.csv
```

**Units in the filename.** The loading rate is in **Pa/s**, while the manuscript
quotes it in MPa/s. So `4e13` in a filename is the same as 4x10^7 MPa/s in
Table 2. The three rates are `4e13`, `6e13`, `8e13`.

Initial densities `9.5668e11`, `1.43e12` and `2.055e12` m^-2 correspond to the
0.957, 1.43 and 2.05 x10^12 m^-2 of Table 2.

## Conditions

| | Values |
|---|---|
| Loading mode | `uniaxial`, `shear` |
| Target stress | 30, 40, 50, 55 MPa |
| Loading rate | 4e13, 6e13, 8e13 Pa/s |
| Initial density | 9.5668e11, 1.43e12, 2.055e12 m^-2 |

Four of the 72 possible combinations were not run, all at the highest target
stress with the lowest loading rate (55 MPa, 4e13 Pa/s): all three shear
densities, and uniaxial at 2.055e12. This leaves 68 runs.

Run `python3 scripts/verify_dataset.py data/raw` to confirm the collection
against this grid.

## Columns

| Column | Meaning | Units |
|---|---|---|
| `step` | simulation step index | -- |
| `time(s)` | accumulated simulation time | s |
| `dt(s)` | time increment | s |
| `strain_eq` | equivalent total strain | -- |
| `sigma_vm(Pa)` | von Mises equivalent stress | Pa |
| `s_xx(Pa)` … `s_xy(Pa)` | Cauchy stress components, order xx yy zz yz zx xy | Pa |
| `density(1/m^2)` | dislocation density | m^-2 |
| `Lpxx` … `Lpzz` | plastic velocity gradient, nine components, row-major | s^-1 |
| `epdot_eq(1/s)` | equivalent plastic strain rate | s^-1 |
| `ep_eq` | accumulated equivalent plastic strain | -- |

## Consistency checks

Every run satisfies, to solver tolerance:

1. `trace(Lp) = 0` -- plastic slip is volume preserving
2. `epdot_eq = sqrt(2/3 * Dp_dev : Dp_dev)` with `Dp = (Lp + Lp^T)/2`
3. For pure shear runs, `sigma_vm = sqrt(3) * s_xy` and all other stress
   components vanish

Verify with:

```
python3 scripts/check_data.py data/raw/*.csv
```
