import numpy as np
import math
import warnings
import sys as _sys
from operator import itemgetter as _itemgetter, eq as _eq
from keyword import iskeyword as _iskeyword


_iter = 100
_xtol = 2e-12
_rtol = 4 * np.finfo(float).eps


def pmv_ppd(tdb, tr, vr, rh, met, clo, wme=0, standard="ISO", **kwargs):
    """Returns Predicted Mean Vote (`PMV`_) and Predicted Percentage of
    Dissatisfied ( `PPD`_) calculated in accordance to main thermal comfort
    Standards. The PMV is an index that predicts the mean value of the thermal
    sensation votes (self-reported perceptions) of a large group of people on a
    sensation scale expressed from –3 to +3 corresponding to the categories:
    cold, cool, slightly cool, neutral, slightly warm, warm, and hot. [1]_

    While the PMV equation is the same for both the ISO and ASHRAE standards, in the
    ASHRAE 55 PMV equation, the SET is used to calculate the cooling effect first,
    this is then subtracted from both the air and mean radiant temperatures, and the
    differences are used as input to the PMV model, while the airspeed is set to 0.1m/s.
    Please read more in the Note below.

    Parameters
    ----------
    tdb : float or array-like
        dry bulb air temperature, default in [°C] in [°F] if `units` = 'IP'
    tr : float or array-like
        mean radiant temperature, default in [°C] in [°F] if `units` = 'IP'
    vr : float or array-like
        relative air speed, default in [m/s] in [fps] if `units` = 'IP'

        Note: vr is the relative air speed caused by body movement and not the air
        speed measured by the air speed sensor. The relative air speed is the sum of the
        average air speed measured by the sensor plus the activity-generated air speed
        (Vag). Where Vag is the activity-generated air speed caused by motion of
        individual body parts. vr can be calculated using the function
        :py:meth:`pythermalcomfort.utilities.v_relative`.
    rh : float or array-like
        relative humidity, [%]
    met : float or array-like
        metabolic rate, [met]
    clo : float or array-like
        clothing insulation, [clo]

        Note: The activity as well as the air speed modify the insulation characteristics
        of the clothing and the adjacent air layer. Consequently, the ISO 7730 states that
        the clothing insulation shall be corrected [2]_. The ASHRAE 55 Standard corrects
        for the effect of the body movement for met equal or higher than 1.2 met using
        the equation clo = Icl × (0.6 + 0.4/met) The dynamic clothing insulation, clo,
        can be calculated using the function
        :py:meth:`pythermalcomfort.utilities.clo_dynamic`.
    wme : float or array-like
        external work, [met] default 0
    standard : {"ISO", "ASHRAE"}
        comfort standard used for calculation

        - If "ISO", then the ISO Equation is used
        - If "ASHRAE", then the ASHRAE Equation is used

        Note: While the PMV equation is the same for both the ISO and ASHRAE standards,
        the ASHRAE Standard Use of the PMV model is limited to air speeds below 0.10
        m/s (20 fpm).
        When air speeds exceed 0.10 m/s (20 fpm), the comfort zone boundaries are
        adjusted based on the SET model.
        This change was indroduced by the `Addendum C to Standard 55-2020`_

    Other Parameters
    ----------------
    units : {'SI', 'IP'}
        select the SI (International System of Units) or the IP (Imperial Units) system.
    limit_inputs : boolean default True
        By default, if the inputs are outsude the standard applicability limits the
        function returns nan. If False returns pmv and ppd values even if input values are
        outside the applicability limits of the model.

        The ASHRAE 55 2020 limits are 10 < tdb [°C] < 40, 10 < tr [°C] < 40,
        0 < vr [m/s] < 2, 1 < met [met] < 4, and 0 < clo [clo] < 1.5.
        The ISO 7730 2005 limits are 10 < tdb [°C] < 30, 10 < tr [°C] < 40,
        0 < vr [m/s] < 1, 0.8 < met [met] < 4, 0 < clo [clo] < 2, and -2 < PMV < 2.
    airspeed_control : boolean default True
        This only applies if standard = "ASHRAE". By default it is assumed that the
        occupant has control over the airspeed. In this case the ASHRAE 55 Standard does
        not imposes any airspeed limits. On the other hand, if the occupant has no control
        over the airspeed the ASHRAE 55 imposes an upper limit for v which varies as a
        function of the operative temperature, for more information please consult the
        Standard.

    Returns
    -------
    pmv : float or array-like
        Predicted Mean Vote
    ppd : float or array-like
        Predicted Percentage of Dissatisfied occupants, [%]

    Notes
    -----
    You can use this function to calculate the `PMV`_ and `PPD`_ in accordance with
    either the ASHRAE 55 2020 Standard [1]_ or the ISO 7730 Standard [2]_.

    .. _PMV: https://en.wikipedia.org/wiki/Thermal_comfort#PMV/PPD_method
    .. _PPD: https://en.wikipedia.org/wiki/Thermal_comfort#PMV/PPD_method
    .. _Addendum C to Standard 55-2020: https://www.ashrae.org/file%20library/technical%20resources/standards%20and%20guidelines/standards%20addenda/55_2020_c_20210430.pdf

    Examples
    --------
    .. code-block:: python

        >>> from pythermalcomfort.models import pmv_ppd
        >>> from pythermalcomfort.utilities import v_relative, clo_dynamic
        >>> tdb = 25
        >>> tr = 25
        >>> rh = 50
        >>> v = 0.1
        >>> met = 1.4
        >>> clo = 0.5
        >>> # calculate relative air speed
        >>> v_r = v_relative(v=v, met=met)
        >>> # calculate dynamic clothing
        >>> clo_d = clo_dynamic(clo=clo, met=met)
        >>> results = pmv_ppd(tdb=tdb, tr=tr, vr=v_r, rh=rh, met=met, clo=clo_d)
        >>> print(results)
        {'pmv': 0.06, 'ppd': 5.1}
        >>> print(results['pmv'])
        -0.06
        >>> # you can also pass an array-like of inputs
        >>> results = pmv_ppd(tdb=[22, 25], tr=tr, vr=v_r, rh=rh, met=met, clo=clo_d)
        >>> print(results)
        {'pmv': array([-0.47,  0.06]), 'ppd': array([9.6, 5.1])}

    Raises
    ------
    StopIteration
        Raised if the number of iterations exceeds the threshold
    ValueError
        The 'standard' function input parameter can only be 'ISO' or 'ASHRAE'
    """
    default_kwargs = {"units": "SI", "limit_inputs": True, "airspeed_control": True}
    kwargs = {**default_kwargs, **kwargs}

    tdb = np.array(tdb)
    tr = np.array(tr)
    vr = np.array(vr)
    met = np.array(met)
    clo = np.array(clo)
    wme = np.array(wme)

    if kwargs["units"].lower() == "ip":
        tdb, tr, vr = units_converter(tdb=tdb, tr=tr, v=vr)

    standard = standard.lower()
    if standard not in ["iso", "ashrae"]:
        raise ValueError(
            "PMV calculations can only be performed in compliance with ISO or ASHRAE "
            "Standards"
        )

    if kwargs["limit_inputs"]:
        (
            tdb_valid,
            tr_valid,
            v_valid,
            met_valid,
            clo_valid,
        ) = check_standard_compliance_array(
            standard,
            tdb=tdb,
            tr=tr,
            v=vr,
            met=met,
            clo=clo,
            airspeed_control=kwargs["airspeed_control"],
        )

    # if v_r is higher than 0.1 follow methodology ASHRAE Appendix H, H3
    ce = 0.0
    if standard == "ashrae":
        ce = np.where(
            vr >= 0.1,
            np.vectorize(cooling_effect, cache=True)(tdb, tr, vr, rh, met, clo, wme),
            0.0,
        )

    tdb = tdb - ce
    tr = tr - ce
    vr = np.where(ce > 0, 0.1, vr)

    pmv_array = pmv_ppd_optimized(tdb, tr, vr, rh, met, clo, wme)

    ppd_array = 100.0 - 95.0 * np.exp(
        -0.03353 * np.power(pmv_array, 4.0) - 0.2179 * np.power(pmv_array, 2.0)
    )

    # Checks that inputs are within the bounds accepted by the model if not return nan
    if kwargs["limit_inputs"]:
        if standard == "ashrae":
            pmv_valid = valid_range(pmv_array, (-100, 100))
        elif standard == "iso":
            pmv_valid = valid_range(pmv_array, (-2, 2))
        all_valid = ~(
            np.isnan(tdb_valid)
            | np.isnan(tr_valid)
            | np.isnan(v_valid)
            | np.isnan(met_valid)
            | np.isnan(clo_valid)
            | np.isnan(pmv_valid)
        )
        pmv_array = np.where(all_valid, pmv_array, np.nan)
        ppd_array = np.where(all_valid, ppd_array, np.nan)

    return {
        "pmv": np.around(pmv_array, 2),
        "ppd": np.around(ppd_array, 1),
    }



def v_relative(v, met):
    """Estimates the relative air speed which combines the average air speed of
    the space plus the relative air speed caused by the body movement. Vag is assumed to
    be 0 for metabolic rates equal and lower than 1 met and otherwise equal to
    Vag = 0.3 (M – 1) (m/s)

    Parameters
    ----------
    v : float or array-like
        air speed measured by the sensor, [m/s]
    met : float
        metabolic rate, [met]

    Returns
    -------
    vr  : float or array-like
        relative air speed, [m/s]
    """

    return np.where(met > 1, np.around(v + 0.3 * (met - 1), 3), v)


#: Met values of typical tasks.
met_typical_tasks = {
    "Sleeping": 0.7,
    "Reclining": 0.8,
    "Seated, quiet": 1.0,
    "Reading, seated": 1.0,
    "Writing": 1.0,
    "Typing": 1.1,
    "Standing, relaxed": 1.2,
    "Filing, seated": 1.2,
    "Flying aircraft, routine": 1.2,
    "Filing, standing": 1.4,
    "Driving a car": 1.5,
    "Walking about": 1.7,
    "Cooking": 1.8,
    "Table sawing": 1.8,
    "Walking 2mph (3.2kmh)": 2.0,
    "Lifting/packing": 2.1,
    "Seated, heavy limb movement": 2.2,
    "Light machine work": 2.2,
    "Flying aircraft, combat": 2.4,
    "Walking 3mph (4.8kmh)": 2.6,
    "House cleaning": 2.7,
    "Driving, heavy vehicle": 3.2,
    "Dancing": 3.4,
    "Calisthenics": 3.5,
    "Walking 4mph (6.4kmh)": 3.8,
    "Tennis": 3.8,
    "Heavy machine work": 4.0,
    "Handling 100lb (45 kg) bags": 4.0,
    "Pick and shovel work": 4.4,
    "Basketball": 6.3,
    "Wrestling": 7.8,
}


def units_converter(from_units="ip", **kwargs):
    """Converts IP values to SI units.

    Parameters
    ----------
    from_units: str
        specify system to convert from
    **kwargs : [t, v]

    Returns
    -------
    converted values in SI units
    """
    results = list()
    if from_units == "ip":
        for key, value in kwargs.items():
            if "tmp" in key or key == "tr" or key == "tdb":
                results.append((value - 32) * 5 / 9)
            if key in ["v", "vr", "vel"]:
                results.append(value / 3.281)
            if key == "area":
                results.append(value / 10.764)
            if key == "pressure":
                results.append(value * 101325)

    elif from_units == "si":
        for key, value in kwargs.items():
            if "tmp" in key or key == "tr" or key == "tdb":
                results.append((value * 9 / 5) + 32)
            if key in ["v", "vr", "vel"]:
                results.append(value * 3.281)
            if key == "area":
                results.append(value * 10.764)
            if key == "pressure":
                results.append(value / 101325)

    return results



def check_standard_compliance_array(standard, **kwargs):
    default_kwargs = {"airspeed_control": True}
    params = {**default_kwargs, **kwargs}

    if standard == "ashrae":  # based on table 7.3.4 ashrae 55 2020
        tdb_valid = valid_range(params["tdb"], (10.0, 40.0))
        tr_valid = valid_range(params["tr"], (10.0, 40.0))
        v_valid = valid_range(params["v"], (0.0, 2.0))

        if not params["airspeed_control"]:
            v_valid = np.where(
                (params["v"] > 0.8) & (params["clo"] < 0.7) & (params["met"] < 1.3),
                np.nan,
                v_valid,
            )
            to = t_o(params["tdb"], params["tr"], params["v"])
            v_limit = 50.49 - 4.4047 * to + 0.096425 * to * to
            v_valid = np.where(
                (23 < to)
                & (to < 25.5)
                & (params["v"] > v_limit)
                & (params["clo"] < 0.7)
                & (params["met"] < 1.3),
                np.nan,
                v_valid,
            )
            v_valid = np.where(
                (to <= 23)
                & (params["v"] > 0.2)
                & (params["clo"] < 0.7)
                & (params["met"] < 1.3),
                np.nan,
                v_valid,
            )

        if "met" in params.keys():
            met_valid = valid_range(params["met"], (1.0, 4.0))
            clo_valid = valid_range(params["clo"], (0.0, 1.5))

            return tdb_valid, tr_valid, v_valid, met_valid, clo_valid

        else:
            return tdb_valid, tr_valid, v_valid

    if standard == "iso":  # based on ISO 7730:2005 page 3
        tdb_valid = valid_range(params["tdb"], (10.0, 30.0))
        tr_valid = valid_range(params["tr"], (10.0, 40.0))
        v_valid = valid_range(params["v"], (0.0, 1.0))
        met_valid = valid_range(params["met"], (0.8, 4.0))
        clo_valid = valid_range(params["clo"], (0.0, 2))

        return tdb_valid, tr_valid, v_valid, met_valid, clo_valid


def cooling_effect(tdb, tr, vr, rh, met, clo, wme=0, units="SI"):
    """Returns the value of the Cooling Effect (`CE`_) calculated in compliance
    with the ASHRAE 55 2020 Standard [1]_. The `CE`_ of the elevated air speed
    is the value that, when subtracted equally from both the average air
    temperature and the mean radiant temperature, yields the same `SET`_ under
    still air as in the first `SET`_ calculation under elevated air speed. The
    cooling effect is calculated only for air speed higher than 0.1 m/s.

    .. _CE: https://en.wikipedia.org/wiki/Thermal_comfort#Cooling_Effect

    Parameters
    ----------
    tdb : float
        dry bulb air temperature, default in [°C] in [°F] if `units` = 'IP'
    tr : float
        mean radiant temperature, default in [°C] in [°F] if `units` = 'IP'
    vr : float
        relative air speed, default in [m/s] in [fps] if `units` = 'IP'

        Note: vr is the relative air speed caused by body movement and not the air
        speed measured by the air speed sensor. The relative air speed is the sum of the
        average air speed measured by the sensor plus the activity-generated air speed
        (Vag). Where Vag is the activity-generated air speed caused by motion of
        individual body parts. vr can be calculated using the function
        :py:meth:`pythermalcomfort.utilities.v_relative`.
    rh : float
        relative humidity, [%]
    met : float
        metabolic rate, [met]
    clo : float
        clothing insulation, [clo]

        Note: The activity as well as the air speed modify the insulation characteristics
        of the clothing and the adjacent air layer. Consequently the ISO 7730 states that
        the clothing insulation shall be corrected [2]_. The ASHRAE 55 Standard corrects
        for the effect of the body movement for met equal or higher than 1.2 met using
        the equation clo = Icl × (0.6 + 0.4/met) The dynamic clothing insulation, clo,
        can be calculated using the function
        :py:meth:`pythermalcomfort.utilities.clo_dynamic`.
    wme : float, default 0
        external work, [met]
    units : {'SI', 'IP'}     select the SI (International System of Units) or the IP (Imperial Units) system.

    Returns
    -------
    ce : float
        Cooling Effect, default in [°C] in [°F] if `units` = 'IP'

    Examples
    --------
    .. code-block:: python

        >>> from pythermalcomfort.models import cooling_effect
        >>> CE = cooling_effect(tdb=25, tr=25, vr=0.3, rh=50, met=1.2, clo=0.5)
        >>> print(CE)
        1.64

        >>> # for users who wants to use the IP system
        >>> CE = cooling_effect(tdb=77, tr=77, vr=1.64, rh=50, met=1, clo=0.6, units="IP")
        >>> print(CE)
        3.74

    Raises
    ------
    ValueError
        If the cooling effect could not be calculated
    """

    if units.lower() == "ip":
        tdb, tr, vr = units_converter(tdb=tdb, tr=tr, v=vr)

    if vr <= 0.1:
        return 0

    still_air_threshold = 0.1

    warnings.simplefilter("ignore")

    initial_set_tmp = set_tmp(
        tdb=tdb,
        tr=tr,
        v=vr,
        rh=rh,
        met=met,
        clo=clo,
        wme=wme,
        round=False,
        calculate_ce=True,
        limit_inputs=False,
    )

    def function(x):
        return (
            set_tmp(
                tdb - x,
                tr - x,
                v=still_air_threshold,
                rh=rh,
                met=met,
                clo=clo,
                wme=wme,
                round=False,
                calculate_ce=True,
                limit_inputs=False,
            )
            - initial_set_tmp
        )

    try:
        ce = brentq(function, 0.0, 15)
    except ValueError:
        ce = 0

    warnings.simplefilter("always")

    if ce == 0:
        warnings.warn(
            "The cooling effect could not be calculated, assuming ce = 0", UserWarning
        )

    if units.lower() == "ip":
        ce = ce / 1.8 * 3.28

    return round(ce, 2)



def pmv_ppd_optimized(tdb, tr, vr, rh, met, clo, wme):

    pa = rh * 10 * math.exp(16.6536 - 4030.183 / (tdb + 235))

    icl = 0.155 * clo  # thermal insulation of the clothing in M2K/W
    m = met * 58.15  # metabolic rate in W/M2
    w = wme * 58.15  # external work in W/M2
    mw = m - w  # internal heat production in the human body
    # calculation of the clothing area factor
    if icl <= 0.078:
        f_cl = 1 + (1.29 * icl)  # ratio of surface clothed body over nude body
    else:
        f_cl = 1.05 + (0.645 * icl)

    # heat transfer coefficient by forced convection
    hcf = 12.1 * math.sqrt(vr)
    hc = hcf  # initialize variable
    taa = tdb + 273
    tra = tr + 273
    t_cla = taa + (35.5 - tdb) / (3.5 * icl + 0.1)

    p1 = icl * f_cl
    p2 = p1 * 3.96
    p3 = p1 * 100
    p4 = p1 * taa
    p5 = (308.7 - 0.028 * mw) + (p2 * (tra / 100.0) ** 4)
    xn = t_cla / 100
    xf = t_cla / 50
    eps = 0.00015

    n = 0
    while abs(xn - xf) > eps:
        xf = (xf + xn) / 2
        hcn = 2.38 * abs(100.0 * xf - taa) ** 0.25
        if hcf > hcn:
            hc = hcf
        else:
            hc = hcn
        xn = (p5 + p4 * hc - p2 * xf ** 4) / (100 + p3 * hc)
        n += 1
        if n > 150:
            raise StopIteration("Max iterations exceeded")

    tcl = 100 * xn - 273

    # heat loss diff. through skin
    hl1 = 3.05 * 0.001 * (5733 - (6.99 * mw) - pa)
    # heat loss by sweating
    if mw > 58.15:
        hl2 = 0.42 * (mw - 58.15)
    else:
        hl2 = 0
    # latent respiration heat loss
    hl3 = 1.7 * 0.00001 * m * (5867 - pa)
    # dry respiration heat loss
    hl4 = 0.0014 * m * (34 - tdb)
    # heat loss by radiation
    hl5 = 3.96 * f_cl * (xn ** 4 - (tra / 100.0) ** 4)
    # heat loss by convection
    hl6 = f_cl * hc * (tcl - tdb)

    ts = 0.303 * math.exp(-0.036 * m) + 0.028
    _pmv = ts * (mw - hl1 - hl2 - hl3 - hl4 - hl5 - hl6)

    return _pmv


def valid_range(x, valid):
    """Filter values based on a valid range."""
    return np.where((x >= valid[0]) & (x <= valid[1]), x, np.nan)


def t_o(tdb, tr, v, standard="ISO"):
    """Calculates operative temperature in accordance with ISO 7726:1998 [5]_

    Parameters
    ----------
    tdb: float
        air temperature, [°C]
    tr: float
        mean radiant temperature, [°C]
    v: float
        air speed, [m/s]
    standard: str (default="ISO")
        either choose between ISO and ASHRAE


    Returns
    -------
    to: float
        operative temperature, [°C]
    """

    if standard.lower() == "iso":
        return (tdb * np.sqrt(10 * v) + tr) / (1 + np.sqrt(10 * v))
    elif standard.lower() == "ashrae":
        a = np.where(v < 0.6, 0.6, 0.7)
        a = np.where(v < 0.2, 0.5, a)
        return a * tdb + (1 - a) * tr


def set_tmp(
    tdb,
    tr,
    v,
    rh,
    met,
    clo,
    wme=0,
    body_surface_area=1.8258,
    p_atm=101325,
    body_position="standing",
    units="SI",
    limit_inputs=True,
    **kwargs,
):
    """
    Calculates the Standard Effective Temperature (SET). The SET is the temperature of
    a hypothetical isothermal environment at 50% (rh), <0.1 m/s (20 fpm) average air
    speed (v), and tr = tdb, in which the total heat loss from the skin of an imaginary occupant
    wearing clothing, standardized for the activity concerned is the same as that
    from a person in the actual environment with actual clothing and activity level. [10]_

    Parameters
    ----------
    tdb : float or array-like
        dry bulb air temperature, default in [°C] in [°F] if `units` = 'IP'
    tr : float or array-like
        mean radiant temperature, default in [°C] in [°F] if `units` = 'IP'
    v : float or array-like
        air speed, default in [m/s] in [fps] if `units` = 'IP'
    rh : float or array-like
        relative humidity, [%]
    met : float or array-like
        metabolic rate, [met]
    clo : float or array-like
        clothing insulation, [clo]
    wme : float or array-like
        external work, [met] default 0
    body_surface_area : float
        body surface area, default value 1.8258 [m2] in [ft2] if `units` = 'IP'

        The body surface area can be calculated using the function
        :py:meth:`pythermalcomfort.utilities.body_surface_area`.
    p_atm : float
        atmospheric pressure, default value 101325 [Pa] in [atm] if `units` = 'IP'
    body_position: str default="standing" or array-like
        select either "sitting" or "standing"
    units : {'SI', 'IP'}
        select the SI (International System of Units) or the IP (Imperial Units) system.
    limit_inputs : boolean default True
        By default, if the inputs are outsude the standard applicability limits the
        function returns nan. If False returns values even if input values are
        outside the applicability limits of the model.
        The ASHRAE 55 2020 limits are 10 < tdb [°C] < 40, 10 < tr [°C] < 40,
        0 < vr [m/s] < 2, 1 < met [met] < 4, and 0 < clo [clo] < 1.5.

    Other Parameters
    ----------------
    round : boolean, deafult True
        if True rounds output value, if False it does not round it

    Returns
    -------
    SET : float or array-like
        Standard effective temperature, [°C]

    Notes
    -----
    You can use this function to calculate the `SET`_ temperature in accordance with
    the ASHRAE 55 2020 Standard [1]_.

    .. _SET: https://en.wikipedia.org/wiki/Thermal_comfort#Standard_effective_temperature

    Examples
    --------
    .. code-block:: python

        >>> from pythermalcomfort.models import set_tmp
        >>> set_tmp(tdb=25, tr=25, v=0.1, rh=50, met=1.2, clo=.5)
        24.3
        >>> set_tmp(tdb=[25, 25], tr=25, v=0.1, rh=50, met=1.2, clo=.5)
        array([24.3, 24.3])

        >>> # for users who wants to use the IP system
        >>> set_tmp(tdb=77, tr=77, v=0.328, rh=50, met=1.2, clo=.5, units='IP')
        75.8

    """
    # When SET is used to calculate CE then h_c is calculated in a slightly different way
    default_kwargs = {"round": True, "calculate_ce": False}
    kwargs = {**default_kwargs, **kwargs}

    if units.lower() == "ip":
        if body_surface_area == 1.8258:
            body_surface_area = 19.65
        if p_atm == 101325:
            p_atm = 1
        tdb, tr, v, body_surface_area, p_atm = units_converter(
            tdb=tdb, tr=tr, v=v, area=body_surface_area, pressure=p_atm
        )

    tdb = np.array(tdb)
    tr = np.array(tr)
    v = np.array(v)
    rh = np.array(rh)
    met = np.array(met)
    clo = np.array(clo)
    wme = np.array(wme)

    set_array = two_nodes(
        tdb=tdb,
        tr=tr,
        v=v,
        rh=rh,
        met=met,
        clo=clo,
        wme=wme,
        body_surface_area=body_surface_area,
        p_atmospheric=p_atm,
        body_position=body_position,
        calculate_ce=kwargs["calculate_ce"],
        round=False,
        output="all",
    )["_set"]

    if units.lower() == "ip":
        set_array = units_converter(tmp=set_array, from_units="si")[0]

    if limit_inputs:
        (
            tdb_valid,
            tr_valid,
            v_valid,
            met_valid,
            clo_valid,
        ) = check_standard_compliance_array(
            "ashrae", tdb=tdb, tr=tr, v=v, met=met, clo=clo
        )
        all_valid = ~(
            np.isnan(tdb_valid)
            | np.isnan(tr_valid)
            | np.isnan(v_valid)
            | np.isnan(met_valid)
            | np.isnan(clo_valid)
        )
        set_array = np.where(all_valid, set_array, np.nan)

    if kwargs["round"]:
        return np.around(set_array, 1)
    else:
        return set_array


def brentq(f, a, b, args=(),
           xtol=_xtol, rtol=_rtol, maxiter=_iter,
           full_output=False, disp=True):
    """
    Find a root of a function in a bracketing interval using Brent's method.

    Uses the classic Brent's method to find a zero of the function `f` on
    the sign changing interval [a , b]. Generally considered the best of the
    rootfinding routines here. It is a safe version of the secant method that
    uses inverse quadratic extrapolation. Brent's method combines root
    bracketing, interval bisection, and inverse quadratic interpolation. It is
    sometimes known as the van Wijngaarden-Dekker-Brent method. Brent (1973)
    claims convergence is guaranteed for functions computable within [a,b].

    [Brent1973]_ provides the classic description of the algorithm. Another
    description can be found in a recent edition of Numerical Recipes, including
    [PressEtal1992]_. A third description is at
    http://mathworld.wolfram.com/BrentsMethod.html. It should be easy to
    understand the algorithm just by reading our code. Our code diverges a bit
    from standard presentations: we choose a different formula for the
    extrapolation step.

    Parameters
    ----------
    f : function
        Python function returning a number. The function :math:`f`
        must be continuous, and :math:`f(a)` and :math:`f(b)` must
        have opposite signs.
    a : scalar
        One end of the bracketing interval :math:`[a, b]`.
    b : scalar
        The other end of the bracketing interval :math:`[a, b]`.
    xtol : number, optional
        The computed root ``x0`` will satisfy ``np.allclose(x, x0,
        atol=xtol, rtol=rtol)``, where ``x`` is the exact root. The
        parameter must be nonnegative. For nice functions, Brent's
        method will often satisfy the above condition with ``xtol/2``
        and ``rtol/2``. [Brent1973]_
    rtol : number, optional
        The computed root ``x0`` will satisfy ``np.allclose(x, x0,
        atol=xtol, rtol=rtol)``, where ``x`` is the exact root. The
        parameter cannot be smaller than its default value of
        ``4*np.finfo(float).eps``. For nice functions, Brent's
        method will often satisfy the above condition with ``xtol/2``
        and ``rtol/2``. [Brent1973]_
    maxiter : int, optional
        If convergence is not achieved in `maxiter` iterations, an error is
        raised. Must be >= 0.
    args : tuple, optional
        Containing extra arguments for the function `f`.
        `f` is called by ``apply(f, (x)+args)``.
    full_output : bool, optional
        If `full_output` is False, the root is returned. If `full_output` is
        True, the return value is ``(x, r)``, where `x` is the root, and `r` is
        a `RootResults` object.
    disp : bool, optional
        If True, raise RuntimeError if the algorithm didn't converge.
        Otherwise, the convergence status is recorded in any `RootResults`
        return object.

    Returns
    -------
    x0 : float
        Zero of `f` between `a` and `b`.
    r : `RootResults` (present if ``full_output = True``)
        Object containing information about the convergence. In particular,
        ``r.converged`` is True if the routine converged.

    Notes
    -----
    `f` must be continuous.  f(a) and f(b) must have opposite signs.

    Related functions fall into several classes:

    multivariate local optimizers
      `fmin`, `fmin_powell`, `fmin_cg`, `fmin_bfgs`, `fmin_ncg`
    nonlinear least squares minimizer
      `leastsq`
    constrained multivariate optimizers
      `fmin_l_bfgs_b`, `fmin_tnc`, `fmin_cobyla`
    global optimizers
      `basinhopping`, `brute`, `differential_evolution`
    local scalar minimizers
      `fminbound`, `brent`, `golden`, `bracket`
    N-D root-finding
      `fsolve`
    1-D root-finding
      `brenth`, `ridder`, `bisect`, `newton`
    scalar fixed-point finder
      `fixed_point`

    References
    ----------
    .. [Brent1973]
       Brent, R. P.,
       *Algorithms for Minimization Without Derivatives*.
       Englewood Cliffs, NJ: Prentice-Hall, 1973. Ch. 3-4.

    .. [PressEtal1992]
       Press, W. H.; Flannery, B. P.; Teukolsky, S. A.; and Vetterling, W. T.
       *Numerical Recipes in FORTRAN: The Art of Scientific Computing*, 2nd ed.
       Cambridge, England: Cambridge University Press, pp. 352-355, 1992.
       Section 9.3:  "Van Wijngaarden-Dekker-Brent Method."

    Examples
    --------
    >>> def f(x):
    ...     return (x**2 - 1)

    >>> from scipy import optimize

    >>> root = optimize.brentq(f, -2, 0)
    >>> root
    -1.0

    >>> root = optimize.brentq(f, 0, 2)
    >>> root
    1.0
    """
    if not isinstance(args, tuple):
        args = (args,)
    maxiter = operator_index(maxiter)
    if xtol <= 0:
        raise ValueError("xtol too small (%g <= 0)" % xtol)
    if rtol < _rtol:
        raise ValueError("rtol too small (%g < %g)" % (rtol, _rtol))
    r = _zeros_brentq(f, a, b, xtol, rtol, maxiter, args, full_output, disp)
    return results_c(full_output, r)


def operator_index(a):
    "Same as a.__index__()."
    return a.__index__()


import typing
def _zeros_brentq() -> typing.Any:
    'a'
    ...



def results_c(full_output, r):
    if full_output:
        x, funcalls, iterations, flag = r
        results = RootResults(root=x,
                              iterations=iterations,
                              function_calls=funcalls,
                              flag=flag)
        return x, results
    else:
        return r

def two_nodes(
    tdb,
    tr,
    v,
    rh,
    met,
    clo,
    wme=0,
    body_surface_area=1.8258,
    p_atmospheric=101325,
    body_position="standing",
    max_skin_blood_flow=90,
    **kwargs,
):
    """Two-node model of human temperature regulation Gagge et al. (1986).

    [10]_ This model it can be used to calculate a variety of indices,
    including:

    * Gagge's version of Fanger's Predicted Mean Vote (PMV). This function uses the Fanger's PMV equations but it replaces the heat loss and gain terms with those calculated by the two node model developed by Gagge et al. (1986) [10]_.

    * PMV SET and the predicted thermal sensation based on SET [10]_. This function is similar in all aspects to the :py:meth:`pythermalcomfort.models.pmv_gagge` however, it uses the :py:meth:`pythermalcomfort.models.set` equation to calculate the dry heat loss by convection.

    * Thermal discomfort (DISC) as the relative thermoregulatory strain necessary to restore a state of comfort and thermal equilibrium by sweating [10]_. DISC is described numerically as: comfortable and pleasant (0), slightly uncomfortable but acceptable (1), uncomfortable and unpleasant (2), very uncomfortable (3), limited tolerance (4), and intolerable (S). The range of each category is ± 0.5 numerically. In the cold, the classical negative category descriptions used for Fanger's PMV apply [10]_.

    * Heat gains and losses via convection, radiation and conduction.

    * The Standard Effective Temperature (SET)

    * The New Effective Temperature (ET)

    * The Predicted  Thermal  Sensation  (TSENS)

    * The Predicted  Percent  Dissatisfied  Due  to  Draft  (PD)

    * Predicted  Percent  Satisfied  With  the  Level  of  Air  Movement"   (PS)

    Parameters
    ----------
    tdb : float or array-like
        dry bulb air temperature, default in [°C] in [°F] if `units` = 'IP'
    tr : float or array-like
        mean radiant temperature, default in [°C] in [°F] if `units` = 'IP'
    v : float or array-like
        air speed, default in [m/s] in [fps] if `units` = 'IP'
    rh : float or array-like
        relative humidity, [%]
    met : float or array-like
        metabolic rate, [met]
    clo : float or array-like
        clothing insulation, [clo]
    wme : float or array-like
        external work, [met] default 0
    body_surface_area : float
        body surface area, default value 1.8258 [m2] in [ft2] if `units` = 'IP'

        The body surface area can be calculated using the function
        :py:meth:`pythermalcomfort.utilities.body_surface_area`.
    p_atmospheric : float
        atmospheric pressure, default value 101325 [Pa] in [atm] if `units` = 'IP'
    body_position: str default="standing" or array-like
        select either "sitting" or "standing"
    max_skin_blood_flow : float
        maximum blood flow from the core to the skin, [L/(hm2)] default 80

    Other Parameters
    ----------------
    round: boolean, default True
        if True rounds output values, if False it does not round them

    Returns
    -------
    e_skin : float or array-like
        Total rate of evaporative heat loss from skin, [W/m2]. Equal to e_rsw + e_diff
    e_rsw : float or array-like
        Rate of evaporative heat loss from sweat evaporation, [W/m2]
    e_diff : float or array-like
        Rate of evaporative heat loss from moisture diffused through the skin, [W/m2]
    e_max : float or array-like
        Maximum rate of evaporative heat loss from skin, [W/m2]
    q_sensible : float or array-like
        Sensible heat loss from skin, [W/m2]
    q_skin : float or array-like
        Total rate of heat loss from skin, [W/m2]. Equal to q_sensible + e_skin
    q_res : float or array-like
        Total rate of heat loss through respiration, [W/m2]
    t_core : float or array-like
        Core temperature, [°C]
    t_skin : float or array-like
        Skin temperature, [°C]
    m_bl : float or array-like
        Skin blood flow, [L/(hm2)]
    m_rsw : float or array-like
        Rate at which regulatory sweat is generated, [mL/h2]
    w : float or array-like
        Skin wettedness, adimensional. Ranges from 0 and 1.
    w_max : float or array-like
        Skin wettedness (w) practical upper limit, adimensional. Ranges from 0 and 1.
    set : float or array-like
        Standard Effective Temperature (SET)
    et : float or array-like
        New Effective Temperature (ET)
    pmv_gagge : float or array-like
        PMV Gagge
    pmv_set : float or array-like
        PMV SET
    pd : float or array-like
        Predicted  Percent  Dissatisfied  Due  to  Draft"
    ps : float or array-like
        Predicted  Percent  Satisfied  With  the  Level  of  Air  Movement
    disc : float or array-like
        Thermal discomfort
    t_sens : float or array-like
        Predicted  Thermal  Sensation

    Examples
    --------
    .. code-block:: python

        >>> from pythermalcomfort.models import two_nodes
        >>> print(two_nodes(tdb=25, tr=25, v=0.3, rh=50, met=1.2, clo=0.5))
        {'e_skin': 15.8, 'e_rsw': 6.5, 'e_diff': 9.3, ... }
        >>> print(two_nodes(tdb=[25, 25], tr=25, v=0.3, rh=50, met=1.2, clo=0.5))
        {'e_skin': array([15.8, 15.8]), 'e_rsw': array([6.5, 6.5]), ... }
    """
    default_kwargs = {
        "round": True,
        "calculate_ce": False,
        "max_sweating": 500,
    }
    kwargs = {**default_kwargs, **kwargs}

    tdb = np.array(tdb)
    tr = np.array(tr)
    v = np.array(v)
    rh = np.array(rh)
    met = np.array(met)
    clo = np.array(clo)
    wme = np.array(wme)
    body_position = np.array(body_position)

    vapor_pressure = rh * p_sat_torr(tdb) / 100

    if kwargs["calculate_ce"]:
        result = two_nodes_optimized_return_set(
            tdb,
            tr,
            v,
            met,
            clo,
            vapor_pressure,
            wme,
            body_surface_area,
            p_atmospheric,
            1,
        )
        return {"_set": result}

    (
        _set,
        e_skin,
        e_rsw,
        e_diff,
        e_max,
        q_sensible,
        q_skin,
        q_res,
        t_core,
        t_skin,
        m_bl,
        m_rsw,
        w,
        w_max,
        et,
        pmv_gagge,
        pmv_set,
        ps,
        disc,
        t_sens,
    ) = np.vectorize(two_nodes_optimized, cache=True)(
        tdb=tdb,
        tr=tr,
        v=v,
        met=met,
        clo=clo,
        vapor_pressure=vapor_pressure,
        wme=wme,
        body_surface_area=body_surface_area,
        p_atmospheric=p_atmospheric,
        body_position=body_position,
        calculate_ce=kwargs["calculate_ce"],
        max_skin_blood_flow=max_skin_blood_flow,
    )

    output = {
        "e_skin": e_skin,
        "e_rsw": e_rsw,
        "e_diff": e_diff,
        "e_max": e_max,
        "q_sensible": q_sensible,
        "q_skin": q_skin,
        "q_res": q_res,
        "t_core": t_core,
        "t_skin": t_skin,
        "m_bl": m_bl,
        "m_rsw": m_rsw,
        "w": w,
        "w_max": w_max,
        "_set": _set,
        "et": et,
        "pmv_gagge": pmv_gagge,
        "pmv_set": pmv_set,
        "ps": ps,
        "disc": disc,
        "t_sens": t_sens,
    }

    for key in output.keys():
        # round the results if needed
        if kwargs["round"]:
            output[key] = np.around(output[key], 1)

    return output

_ECONVERGED = 0
_ESIGNERR = -1
_ECONVERR = -2
_EVALUEERR = -3
_EINPROGRESS = 1

CONVERGED = 'converged'
SIGNERR = 'sign error'
CONVERR = 'convergence error'
VALUEERR = 'value error'
INPROGRESS = 'No error'
flag_map = {_ECONVERGED: CONVERGED, _ESIGNERR: SIGNERR, _ECONVERR: CONVERR,
            _EVALUEERR: VALUEERR, _EINPROGRESS: INPROGRESS}

class RootResults(object):
    """Represents the root finding result.

    Attributes
    ----------
    root : float
        Estimated root location.
    iterations : int
        Number of iterations needed to find the root.
    function_calls : int
        Number of times the function was called.
    converged : bool
        True if the routine converged.
    flag : str
        Description of the cause of termination.

    """

    def __init__(self, root, iterations, function_calls, flag):
        self.root = root
        self.iterations = iterations
        self.function_calls = function_calls
        self.converged = flag == _ECONVERGED
        self.flag = None
        try:
            self.flag = flag_map[flag]
        except KeyError:
            self.flag = 'unknown error %d' % (flag,)

    def __repr__(self):
        attrs = ['converged', 'flag', 'function_calls',
                 'iterations', 'root']
        m = max(map(len, attrs)) + 1
        return '\n'.join([a.rjust(m) + ': ' + repr(getattr(self, a))
                          for a in attrs])


def results_c(full_output, r):
    if full_output:
        x, funcalls, iterations, flag = r
        results = RootResults(root=x,
                              iterations=iterations,
                              function_calls=funcalls,
                              flag=flag)
        return x, results
    else:
        return r


def _results_select(full_output, r):
    """Select from a tuple of (root, funccalls, iterations, flag)"""
    x, funcalls, iterations, flag = r
    if full_output:
        results = RootResults(root=x,
                              iterations=iterations,
                              function_calls=funcalls,
                              flag=flag)
        return x, results
    return x


def newton(func, x0, fprime=None, args=(), tol=1.48e-8, maxiter=50,
           fprime2=None, x1=None, rtol=0.0,
           full_output=False, disp=True):
    """
    Find a zero of a real or complex function using the Newton-Raphson
    (or secant or Halley's) method.

    Find a zero of the function `func` given a nearby starting point `x0`.
    The Newton-Raphson method is used if the derivative `fprime` of `func`
    is provided, otherwise the secant method is used. If the second order
    derivative `fprime2` of `func` is also provided, then Halley's method is
    used.

    If `x0` is a sequence with more than one item, then `newton` returns an
    array, and `func` must be vectorized and return a sequence or array of the
    same shape as its first argument. If `fprime` or `fprime2` is given, then
    its return must also have the same shape.

    Parameters
    ----------
    func : callable
        The function whose zero is wanted. It must be a function of a
        single variable of the form ``f(x,a,b,c...)``, where ``a,b,c...``
        are extra arguments that can be passed in the `args` parameter.
    x0 : float, sequence, or ndarray
        An initial estimate of the zero that should be somewhere near the
        actual zero. If not scalar, then `func` must be vectorized and return
        a sequence or array of the same shape as its first argument.
    fprime : callable, optional
        The derivative of the function when available and convenient. If it
        is None (default), then the secant method is used.
    args : tuple, optional
        Extra arguments to be used in the function call.
    tol : float, optional
        The allowable error of the zero value. If `func` is complex-valued,
        a larger `tol` is recommended as both the real and imaginary parts
        of `x` contribute to ``|x - x0|``.
    maxiter : int, optional
        Maximum number of iterations.
    fprime2 : callable, optional
        The second order derivative of the function when available and
        convenient. If it is None (default), then the normal Newton-Raphson
        or the secant method is used. If it is not None, then Halley's method
        is used.
    x1 : float, optional
        Another estimate of the zero that should be somewhere near the
        actual zero. Used if `fprime` is not provided.
    rtol : float, optional
        Tolerance (relative) for termination.
    full_output : bool, optional
        If `full_output` is False (default), the root is returned.
        If True and `x0` is scalar, the return value is ``(x, r)``, where ``x``
        is the root and ``r`` is a `RootResults` object.
        If True and `x0` is non-scalar, the return value is ``(x, converged,
        zero_der)`` (see Returns section for details).
    disp : bool, optional
        If True, raise a RuntimeError if the algorithm didn't converge, with
        the error message containing the number of iterations and current
        function value. Otherwise, the convergence status is recorded in a
        `RootResults` return object.
        Ignored if `x0` is not scalar.
        *Note: this has little to do with displaying, however,
        the `disp` keyword cannot be renamed for backwards compatibility.*

    Returns
    -------
    root : float, sequence, or ndarray
        Estimated location where function is zero.
    r : `RootResults`, optional
        Present if ``full_output=True`` and `x0` is scalar.
        Object containing information about the convergence. In particular,
        ``r.converged`` is True if the routine converged.
    converged : ndarray of bool, optional
        Present if ``full_output=True`` and `x0` is non-scalar.
        For vector functions, indicates which elements converged successfully.
    zero_der : ndarray of bool, optional
        Present if ``full_output=True`` and `x0` is non-scalar.
        For vector functions, indicates which elements had a zero derivative.

    See Also
    --------
    brentq, brenth, ridder, bisect
    fsolve : find zeros in N dimensions.

    Notes
    -----
    The convergence rate of the Newton-Raphson method is quadratic,
    the Halley method is cubic, and the secant method is
    sub-quadratic. This means that if the function is well-behaved
    the actual error in the estimated zero after the nth iteration
    is approximately the square (cube for Halley) of the error
    after the (n-1)th step. However, the stopping criterion used
    here is the step size and there is no guarantee that a zero
    has been found. Consequently, the result should be verified.
    Safer algorithms are brentq, brenth, ridder, and bisect,
    but they all require that the root first be bracketed in an
    interval where the function changes sign. The brentq algorithm
    is recommended for general use in one dimensional problems
    when such an interval has been found.

    When `newton` is used with arrays, it is best suited for the following
    types of problems:

    * The initial guesses, `x0`, are all relatively the same distance from
      the roots.
    * Some or all of the extra arguments, `args`, are also arrays so that a
      class of similar problems can be solved together.
    * The size of the initial guesses, `x0`, is larger than O(100) elements.
      Otherwise, a naive loop may perform as well or better than a vector.

    Examples
    --------
    >>> from scipy import optimize
    >>> import matplotlib.pyplot as plt

    >>> def f(x):
    ...     return (x**3 - 1)  # only one real root at x = 1

    ``fprime`` is not provided, use the secant method:

    >>> root = optimize.newton(f, 1.5)
    >>> root
    1.0000000000000016
    >>> root = optimize.newton(f, 1.5, fprime2=lambda x: 6 * x)
    >>> root
    1.0000000000000016

    Only ``fprime`` is provided, use the Newton-Raphson method:

    >>> root = optimize.newton(f, 1.5, fprime=lambda x: 3 * x**2)
    >>> root
    1.0

    Both ``fprime2`` and ``fprime`` are provided, use Halley's method:

    >>> root = optimize.newton(f, 1.5, fprime=lambda x: 3 * x**2,
    ...                        fprime2=lambda x: 6 * x)
    >>> root
    1.0

    When we want to find zeros for a set of related starting values and/or
    function parameters, we can provide both of those as an array of inputs:

    >>> f = lambda x, a: x**3 - a
    >>> fder = lambda x, a: 3 * x**2
    >>> np.random.seed(4321)
    >>> x = np.random.randn(100)
    >>> a = np.arange(-50, 50)
    >>> vec_res = optimize.newton(f, x, fprime=fder, args=(a, ))

    The above is the equivalent of solving for each value in ``(x, a)``
    separately in a for-loop, just faster:

    >>> loop_res = [optimize.newton(f, x0, fprime=fder, args=(a0,))
    ...             for x0, a0 in zip(x, a)]
    >>> np.allclose(vec_res, loop_res)
    True

    Plot the results found for all values of ``a``:

    >>> analytical_result = np.sign(a) * np.abs(a)**(1/3)
    >>> fig = plt.figure()
    >>> ax = fig.add_subplot(111)
    >>> ax.plot(a, analytical_result, 'o')
    >>> ax.plot(a, vec_res, '.')
    >>> ax.set_xlabel('$a$')
    >>> ax.set_ylabel('$x$ where $f(x, a)=0$')
    >>> plt.show()

    """
    if tol <= 0:
        raise ValueError("tol too small (%g <= 0)" % tol)
    maxiter = operator_index(maxiter)
    if maxiter < 1:
        raise ValueError("maxiter must be greater than 0")
    if np.size(x0) > 1:
        return _array_newton(func, x0, fprime, args, tol, maxiter, fprime2,
                             full_output)

    # Convert to float (don't use float(x0); this works also for complex x0)
    p0 = 1.0 * x0
    funcalls = 0
    if fprime is not None:
        # Newton-Raphson method
        for itr in range(maxiter):
            # first evaluate fval
            fval = func(p0, *args)
            funcalls += 1
            # If fval is 0, a root has been found, then terminate
            if fval == 0:
                return _results_select(
                    full_output, (p0, funcalls, itr, _ECONVERGED))
            fder = fprime(p0, *args)
            funcalls += 1
            if fder == 0:
                msg = "Derivative was zero."
                if disp:
                    msg += (
                        " Failed to converge after %d iterations, value is %s."
                        % (itr + 1, p0))
                    raise RuntimeError(msg)
                warnings.warn(msg, RuntimeWarning)
                return _results_select(
                    full_output, (p0, funcalls, itr + 1, _ECONVERR))
            newton_step = fval / fder
            if fprime2:
                fder2 = fprime2(p0, *args)
                funcalls += 1
                # Halley's method:
                #   newton_step /= (1.0 - 0.5 * newton_step * fder2 / fder)
                # Only do it if denominator stays close enough to 1
                # Rationale: If 1-adj < 0, then Halley sends x in the
                # opposite direction to Newton. Doesn't happen if x is close
                # enough to root.
                adj = newton_step * fder2 / fder / 2
                if np.abs(adj) < 1:
                    newton_step /= 1.0 - adj
            p = p0 - newton_step
            if np.isclose(p, p0, rtol=rtol, atol=tol):
                return _results_select(
                    full_output, (p, funcalls, itr + 1, _ECONVERGED))
            p0 = p
    else:
        # Secant method
        if x1 is not None:
            if x1 == x0:
                raise ValueError("x1 and x0 must be different")
            p1 = x1
        else:
            eps = 1e-4
            p1 = x0 * (1 + eps)
            p1 += (eps if p1 >= 0 else -eps)
        q0 = func(p0, *args)
        funcalls += 1
        q1 = func(p1, *args)
        funcalls += 1
        if abs(q1) < abs(q0):
            p0, p1, q0, q1 = p1, p0, q1, q0
        for itr in range(maxiter):
            if q1 == q0:
                if p1 != p0:
                    msg = "Tolerance of %s reached." % (p1 - p0)
                    if disp:
                        msg += (
                            " Failed to converge after %d iterations, value is %s."
                            % (itr + 1, p1))
                        raise RuntimeError(msg)
                    warnings.warn(msg, RuntimeWarning)
                p = (p1 + p0) / 2.0
                return _results_select(
                    full_output, (p, funcalls, itr + 1, _ECONVERGED))
            else:
                if abs(q1) > abs(q0):
                    p = (-q0 / q1 * p1 + p0) / (1 - q0 / q1)
                else:
                    p = (-q1 / q0 * p0 + p1) / (1 - q1 / q0)
            if np.isclose(p, p1, rtol=rtol, atol=tol):
                return _results_select(
                    full_output, (p, funcalls, itr + 1, _ECONVERGED))
            p0, q0 = p1, q1
            p1 = p
            q1 = func(p1, *args)
            funcalls += 1

    if disp:
        msg = ("Failed to converge after %d iterations, value is %s."
               % (itr + 1, p))
        raise RuntimeError(msg)

    return _results_select(full_output, (p, funcalls, itr + 1, _ECONVERR))



def two_nodes_optimized_return_set(
    tdb,
    tr,
    v,
    met,
    clo,
    vapor_pressure,
    wme,
    body_surface_area,
    p_atmospheric,
    body_position,
):
    return two_nodes_optimized(
        tdb,
        tr,
        v,
        met,
        clo,
        vapor_pressure,
        wme,
        body_surface_area,
        p_atmospheric,
        body_position,
        True,
    )[0]



def p_sat_torr(tdb):
    """Estimates the saturation vapor pressure in [torr]

    Parameters
    ----------
    tdb : float
        dry bulb air temperature, [C]

    Returns
    -------
    p_sat  : float
        saturation vapor pressure [torr]
    """
    return np.exp(18.6686 - 4030.183 / (tdb + 235.0))


def two_nodes_optimized(
    tdb,
    tr,
    v,
    met,
    clo,
    vapor_pressure,
    wme,
    body_surface_area,
    p_atmospheric,
    body_position,
    calculate_ce=False,
    max_skin_blood_flow=90,
    max_sweating=500,
):
    # Initial variables as defined in the ASHRAE 55-2020
    air_speed = max(v, 0.1)
    k_clo = 0.25
    body_weight = 69.9  # body weight in kg
    met_factor = 58.2  # met conversion factor
    sbc = 0.000000056697  # Stefan-Boltzmann constant (W/m2K4)
    c_sw = 170  # driving coefficient for regulatory sweating
    c_dil = 200  # driving coefficient for vasodilation ashrae says 50 see page 195
    c_str = 0.5  # driving coefficient for vasoconstriction

    temp_skin_neutral = 33.7
    temp_core_neutral = 36.8
    alfa = 0.1
    temp_body_neutral = alfa * temp_skin_neutral + (1 - alfa) * temp_core_neutral
    skin_blood_flow_neutral = 6.3

    t_skin = temp_skin_neutral
    t_core = temp_core_neutral
    m_bl = skin_blood_flow_neutral

    # initialize some variables
    e_skin = 0.1 * met  # total evaporative heat loss, W
    q_sensible = 0  # total sensible heat loss, W
    w = 0  # skin wettedness
    _set = 0  # standard effective temperature
    e_rsw = 0  # heat lost by vaporization sweat
    e_diff = 0  # vapor diffusion through skin
    e_max = 0  # maximum evaporative capacity
    m_rsw = 0  # regulatory sweating
    q_res = 0  # heat loss due to respiration
    et = 0  # effective temperature
    e_req = 0  # evaporative heat loss required for tmp regulation
    r_ea = 0
    r_ecl = 0
    c_res = 0  # convective heat loss respiration

    pressure_in_atmospheres = p_atmospheric / 101325
    length_time_simulation = 60  # length time simulation
    n_simulation = 0

    r_clo = 0.155 * clo  # thermal resistance of clothing, C M^2 /W
    f_a_cl = 1.0 + 0.15 * clo  # increase in body surface area due to clothing
    lr = 2.2 / pressure_in_atmospheres  # Lewis ratio
    rm = (met - wme) * met_factor  # metabolic rate
    m = met * met_factor  # metabolic rate

    e_comfort = 0.42 * (rm - met_factor)  # evaporative heat loss during comfort
    if e_comfort < 0:
        e_comfort = 0

    if clo <= 0:
        w_max = 0.38 * pow(air_speed, -0.29)  # critical skin wettedness
        i_cl = 1.0  # permeation efficiency of water vapour through the clothing layer
    else:
        w_max = 0.59 * pow(air_speed, -0.08)  # critical skin wettedness
        i_cl = 0.45  # permeation efficiency of water vapour through the clothing layer

    # h_cc corrected convective heat transfer coefficient
    h_cc = 3.0 * pow(pressure_in_atmospheres, 0.53)
    # h_fc forced convective heat transfer coefficient, W/(m2 °C)
    h_fc = 8.600001 * pow((air_speed * pressure_in_atmospheres), 0.53)
    h_cc = max(h_cc, h_fc)
    if not calculate_ce and met > 0.85:
        h_c_met = 5.66 * (met - 0.85) ** 0.39
        h_cc = max(h_cc, h_c_met)

    h_r = 4.7  # linearized radiative heat transfer coefficient
    h_t = h_r + h_cc  # sum of convective and radiant heat transfer coefficient W/(m2*K)
    r_a = 1.0 / (f_a_cl * h_t)  # resistance of air layer to dry heat
    t_op = (h_r * tr + h_cc * tdb) / h_t  # operative temperature

    t_body = alfa * t_skin + (1 - alfa) * t_core  # mean body temperature, °C

    # respiration
    q_res = 0.0023 * m * (44.0 - vapor_pressure)  # latent heat loss due to respiration
    c_res = 0.0014 * m * (34.0 - tdb)  # sensible convective heat loss respiration

    while n_simulation < length_time_simulation:

        n_simulation += 1

        iteration_limit = 150  # for following while loop
        # t_cl temperature of the outer surface of clothing
        t_cl = (r_a * t_skin + r_clo * t_op) / (r_a + r_clo)  # initial guess
        n_iterations = 0
        tc_converged = False

        while not tc_converged:

            # 0.95 is the clothing emissivity from ASHRAE fundamentals Ch. 9.7 Eq. 35
            if body_position == "sitting":
                # 0.7 ratio between radiation area of the body and the body area
                h_r = 4.0 * 0.95 * sbc * ((t_cl + tr) / 2.0 + 273.15) ** 3.0 * 0.7
            else:  # if standing
                # 0.73 ratio between radiation area of the body and the body area
                h_r = 4.0 * 0.95 * sbc * ((t_cl + tr) / 2.0 + 273.15) ** 3.0 * 0.73
            h_t = h_r + h_cc
            r_a = 1.0 / (f_a_cl * h_t)
            t_op = (h_r * tr + h_cc * tdb) / h_t
            t_cl_new = (r_a * t_skin + r_clo * t_op) / (r_a + r_clo)
            if abs(t_cl_new - t_cl) <= 0.01:
                tc_converged = True
            t_cl = t_cl_new
            n_iterations += 1

            if n_iterations > iteration_limit:
                raise StopIteration("Max iterations exceeded")

        q_sensible = (t_skin - t_op) / (r_a + r_clo)  # total sensible heat loss, W
        # hf_cs rate of energy transport between core and skin, W
        # 5.28 is the average body tissue conductance in W/(m2 C)
        # 1.163 is the thermal capacity of blood in Wh/(L C)
        hf_cs = (t_core - t_skin) * (5.28 + 1.163 * m_bl)
        s_core = m - hf_cs - q_res - c_res - wme  # rate of energy storage in the core
        s_skin = hf_cs - q_sensible - e_skin  # rate of energy storage in the skin
        tc_sk = 0.97 * alfa * body_weight  # thermal capacity skin
        tc_cr = 0.97 * (1 - alfa) * body_weight  # thermal capacity core
        d_t_sk = (s_skin * body_surface_area) / (
            tc_sk * 60.0
        )  # rate of change skin temperature °C per minute
        d_t_cr = (
            s_core * body_surface_area / (tc_cr * 60.0)
        )  # rate of change core temperature °C per minute
        t_skin = t_skin + d_t_sk
        t_core = t_core + d_t_cr
        t_body = alfa * t_skin + (1 - alfa) * t_core
        # sk_sig thermoregulatory control signal from the skin
        sk_sig = t_skin - temp_skin_neutral
        warm_sk = (sk_sig > 0) * sk_sig  # vasodilation signal
        colds = ((-1.0 * sk_sig) > 0) * (-1.0 * sk_sig)  # vasoconstriction signal
        # c_reg_sig thermoregulatory control signal from the skin, °C
        c_reg_sig = t_core - temp_core_neutral
        # c_warm vasodilation signal
        c_warm = (c_reg_sig > 0) * c_reg_sig
        # c_cold vasoconstriction signal
        c_cold = ((-1.0 * c_reg_sig) > 0) * (-1.0 * c_reg_sig)
        # bd_sig thermoregulatory control signal from the body
        bd_sig = t_body - temp_body_neutral
        warm_b = (bd_sig > 0) * bd_sig
        m_bl = (skin_blood_flow_neutral + c_dil * c_warm) / (1 + c_str * colds)
        if m_bl > max_skin_blood_flow:
            m_bl = max_skin_blood_flow
        if m_bl < 0.5:
            m_bl = 0.5
        m_rsw = c_sw * warm_b * math.exp(warm_sk / 10.7)  # regulatory sweating
        if m_rsw > max_sweating:
            m_rsw = max_sweating
        e_rsw = 0.68 * m_rsw  # heat lost by vaporization sweat
        r_ea = 1.0 / (lr * f_a_cl * h_cc)  # evaporative resistance air layer
        r_ecl = r_clo / (lr * i_cl)
        e_req = (
            rm - q_res - c_res - q_sensible
        )  # evaporative heat loss required for tmp regulation
        e_max = (math.exp(18.6686 - 4030.183 / (t_skin + 235.0)) - vapor_pressure) / (
            r_ea + r_ecl
        )
        p_rsw = e_rsw / e_max  # ratio heat loss sweating to max heat loss sweating
        w = 0.06 + 0.94 * p_rsw  # skin wetness
        e_diff = w * e_max - e_rsw  # vapor diffusion through skin
        if w > w_max:
            w = w_max
            p_rsw = w_max / 0.94
            e_rsw = p_rsw * e_max
            e_diff = 0.06 * (1.0 - p_rsw) * e_max
        if e_max < 0:
            e_diff = 0
            e_rsw = 0
            w = w_max
        e_skin = (
            e_rsw + e_diff
        )  # total evaporative heat loss sweating and vapor diffusion
        met_shivering = 19.4 * colds * c_cold  # met shivering W/m2
        m = rm + met_shivering
        alfa = 0.0417737 + 0.7451833 / (m_bl + 0.585417)

    q_skin = q_sensible + e_skin  # total heat loss from skin, W
    # p_s_sk saturation vapour pressure of water of the skin
    p_s_sk = math.exp(18.6686 - 4030.183 / (t_skin + 235.0))

    # standard environment - where _s at end of the variable names stands for standard
    h_r_s = h_r  # standard environment radiative heat transfer coefficient

    h_c_s = 3.0 * pow(pressure_in_atmospheres, 0.53)
    if not calculate_ce and met > 0.85:
        h_c_met = 5.66 * (met - 0.85) ** 0.39
        h_c_s = max(h_c_s, h_c_met)
    if h_c_s < 3.0:
        h_c_s = 3.0

    h_t_s = (
        h_c_s + h_r_s
    )  # sum of convective and radiant heat transfer coefficient W/(m2*K)
    r_clo_s = (
        1.52 / ((met - wme / met_factor) + 0.6944) - 0.1835
    )  # thermal resistance of clothing, °C M^2 /W
    r_cl_s = 0.155 * r_clo_s  # thermal insulation of the clothing in M2K/W
    f_a_cl_s = 1.0 + k_clo * r_clo_s  # increase in body surface area due to clothing
    f_cl_s = 1.0 / (
        1.0 + 0.155 * f_a_cl_s * h_t_s * r_clo_s
    )  # ratio of surface clothed body over nude body
    i_m_s = 0.45  # permeation efficiency of water vapour through the clothing layer
    i_cl_s = (
        i_m_s * h_c_s / h_t_s * (1 - f_cl_s) / (h_c_s / h_t_s - f_cl_s * i_m_s)
    )  # clothing vapor permeation efficiency
    r_a_s = 1.0 / (f_a_cl_s * h_t_s)  # resistance of air layer to dry heat
    r_ea_s = 1.0 / (lr * f_a_cl_s * h_c_s)
    r_ecl_s = r_cl_s / (lr * i_cl_s)
    h_d_s = 1.0 / (r_a_s + r_cl_s)
    h_e_s = 1.0 / (r_ea_s + r_ecl_s)

    # calculate Standard Effective Temperature (SET)
    delta = 0.0001
    dx = 100.0
    set_old = round(t_skin - q_skin / h_d_s, 2)
    while abs(dx) > 0.01:
        err_1 = (
            q_skin
            - h_d_s * (t_skin - set_old)
            - w
            * h_e_s
            * (p_s_sk - 0.5 * (math.exp(18.6686 - 4030.183 / (set_old + 235.0))))
        )
        err_2 = (
            q_skin
            - h_d_s * (t_skin - (set_old + delta))
            - w
            * h_e_s
            * (
                p_s_sk
                - 0.5 * (math.exp(18.6686 - 4030.183 / (set_old + delta + 235.0)))
            )
        )
        _set = set_old - delta * err_1 / (err_2 - err_1)
        dx = _set - set_old
        set_old = _set

    # calculate Effective Temperature (ET)
    h_d = 1 / (r_a + r_clo)
    h_e = 1 / (r_ea + r_ecl)
    et_old = t_skin - q_skin / h_d
    delta = 0.0001
    dx = 100.0
    while abs(dx) > 0.01:
        err_1 = (
            q_skin
            - h_d * (t_skin - et_old)
            - w
            * h_e
            * (p_s_sk - 0.5 * (math.exp(18.6686 - 4030.183 / (et_old + 235.0))))
        )
        err_2 = (
            q_skin
            - h_d * (t_skin - (et_old + delta))
            - w
            * h_e
            * (p_s_sk - 0.5 * (math.exp(18.6686 - 4030.183 / (et_old + delta + 235.0))))
        )
        et = et_old - delta * err_1 / (err_2 - err_1)
        dx = et - et_old
        et_old = et

    tbm_l = (0.194 / 58.15) * rm + 36.301  # lower limit for evaporative regulation
    tbm_h = (0.347 / 58.15) * rm + 36.669  # upper limit for evaporative regulation

    t_sens = 0.4685 * (t_body - tbm_l)  # predicted thermal sensation
    if (t_body >= tbm_l) & (t_body < tbm_h):
        t_sens = w_max * 4.7 * (t_body - tbm_l) / (tbm_h - tbm_l)
    elif t_body >= tbm_h:
        t_sens = w_max * 4.7 + 0.4685 * (t_body - tbm_h)

    disc = (
        4.7 * (e_rsw - e_comfort) / (e_max * w_max - e_comfort - e_diff)
    )  # predicted thermal discomfort
    if disc <= 0:
        disc = t_sens

    # PMV Gagge
    pmv_gagge = (0.303 * math.exp(-0.036 * m) + 0.028) * (e_req - e_comfort - e_diff)

    # PMV SET
    dry_set = h_d_s * (t_skin - _set)
    e_req_set = rm - c_res - q_res - dry_set
    pmv_set = (0.303 * math.exp(-0.036 * m) + 0.028) * (e_req_set - e_comfort - e_diff)

    # Predicted  Percent  Satisfied  With  the  Level  of  Air  Movement"
    ps = 100 * (1.13 * (t_op ** 0.5) - 0.24 * t_op + 2.7 * (v ** 0.5) - 0.99 * v)

    return (
        _set,
        e_skin,
        e_rsw,
        e_diff,
        e_max,
        q_sensible,
        q_skin,
        q_res,
        t_core,
        t_skin,
        m_bl,
        m_rsw,
        w,
        w_max,
        et,
        pmv_gagge,
        pmv_set,
        ps,
        disc,
        t_sens,
    )


def _array_newton(func, x0, fprime, args, tol, maxiter, fprime2, full_output):
    """
    A vectorized version of Newton, Halley, and secant methods for arrays.

    Do not use this method directly. This method is called from `newton`
    when ``np.size(x0) > 1`` is ``True``. For docstring, see `newton`.
    """
    # Explicitly copy `x0` as `p` will be modified inplace, but the
    # user's array should not be altered.
    p = np.array(x0, copy=True)

    failures = np.ones_like(p, dtype=bool)
    nz_der = np.ones_like(failures)
    if fprime is not None:
        # Newton-Raphson method
        for iteration in range(maxiter):
            # first evaluate fval
            fval = np.asarray(func(p, *args))
            # If all fval are 0, all roots have been found, then terminate
            if not fval.any():
                failures = fval.astype(bool)
                break
            fder = np.asarray(fprime(p, *args))
            nz_der = (fder != 0)
            # stop iterating if all derivatives are zero
            if not nz_der.any():
                break
            # Newton step
            dp = fval[nz_der] / fder[nz_der]
            if fprime2 is not None:
                fder2 = np.asarray(fprime2(p, *args))
                dp = dp / (1.0 - 0.5 * dp * fder2[nz_der] / fder[nz_der])
            # only update nonzero derivatives
            p = np.asarray(p, dtype=np.result_type(p, dp, np.float64))
            p[nz_der] -= dp
            failures[nz_der] = np.abs(dp) >= tol  # items not yet converged
            # stop iterating if there aren't any failures, not incl zero der
            if not failures[nz_der].any():
                break
    else:
        # Secant method
        dx = np.finfo(float).eps**0.33
        p1 = p * (1 + dx) + np.where(p >= 0, dx, -dx)
        q0 = np.asarray(func(p, *args))
        q1 = np.asarray(func(p1, *args))
        active = np.ones_like(p, dtype=bool)
        for iteration in range(maxiter):
            nz_der = (q1 != q0)
            # stop iterating if all derivatives are zero
            if not nz_der.any():
                p = (p1 + p) / 2.0
                break
            # Secant Step
            dp = (q1 * (p1 - p))[nz_der] / (q1 - q0)[nz_der]
            # only update nonzero derivatives
            p = np.asarray(p, dtype=np.result_type(p, p1, dp, np.float64))
            p[nz_der] = p1[nz_der] - dp
            active_zero_der = ~nz_der & active
            p[active_zero_der] = (p1 + p)[active_zero_der] / 2.0
            active &= nz_der  # don't assign zero derivatives again
            failures[nz_der] = np.abs(dp) >= tol  # not yet converged
            # stop iterating if there aren't any failures, not incl zero der
            if not failures[nz_der].any():
                break
            p1, p = p, p1
            q0 = q1
            q1 = np.asarray(func(p1, *args))

    zero_der = ~nz_der & failures  # don't include converged with zero-ders
    if zero_der.any():
        # Secant warnings
        if fprime is None:
            nonzero_dp = (p1 != p)
            # non-zero dp, but infinite newton step
            zero_der_nz_dp = (zero_der & nonzero_dp)
            if zero_der_nz_dp.any():
                rms = np.sqrt(
                    sum((p1[zero_der_nz_dp] - p[zero_der_nz_dp]) ** 2)
                )
                warnings.warn(
                    'RMS of {:g} reached'.format(rms), RuntimeWarning)
        # Newton or Halley warnings
        else:
            all_or_some = 'all' if zero_der.all() else 'some'
            msg = '{:s} derivatives were zero'.format(all_or_some)
            warnings.warn(msg, RuntimeWarning)
    elif failures.any():
        all_or_some = 'all' if failures.all() else 'some'
        msg = '{0:s} failed to converge after {1:d} iterations'.format(
            all_or_some, maxiter
        )
        if failures.all():
            raise RuntimeError(msg)
        warnings.warn(msg, RuntimeWarning)

    if full_output:
        result = namedtuple('result', ('root', 'converged', 'zero_der'))
        p = result(p, ~failures, zero_der)

    return p

try:
    from _collections import _tuplegetter
except ImportError:
    _tuplegetter = lambda index, doc: property(_itemgetter(index), doc=doc)


def namedtuple(typename, field_names, *, rename=False, defaults=None, module=None):
    """Returns a new subclass of tuple with named fields.

    >>> Point = namedtuple('Point', ['x', 'y'])
    >>> Point.__doc__                   # docstring for the new class
    'Point(x, y)'
    >>> p = Point(11, y=22)             # instantiate with positional args or keywords
    >>> p[0] + p[1]                     # indexable like a plain tuple
    33
    >>> x, y = p                        # unpack like a regular tuple
    >>> x, y
    (11, 22)
    >>> p.x + p.y                       # fields also accessible by name
    33
    >>> d = p._asdict()                 # convert to a dictionary
    >>> d['x']
    11
    >>> Point(**d)                      # convert from a dictionary
    Point(x=11, y=22)
    >>> p._replace(x=100)               # _replace() is like str.replace() but targets named fields
    Point(x=100, y=22)

    """

    # Validate the field names.  At the user's option, either generate an error
    # message or automatically replace the field name with a valid name.
    if isinstance(field_names, str):
        field_names = field_names.replace(',', ' ').split()
    field_names = list(map(str, field_names))
    typename = _sys.intern(str(typename))

    if rename:
        seen = set()
        for index, name in enumerate(field_names):
            if (not name.isidentifier()
                or _iskeyword(name)
                or name.startswith('_')
                or name in seen):
                field_names[index] = f'_{index}'
            seen.add(name)

    for name in [typename] + field_names:
        if type(name) is not str:
            raise TypeError('Type names and field names must be strings')
        if not name.isidentifier():
            raise ValueError('Type names and field names must be valid '
                             f'identifiers: {name!r}')
        if _iskeyword(name):
            raise ValueError('Type names and field names cannot be a '
                             f'keyword: {name!r}')

    seen = set()
    for name in field_names:
        if name.startswith('_') and not rename:
            raise ValueError('Field names cannot start with an underscore: '
                             f'{name!r}')
        if name in seen:
            raise ValueError(f'Encountered duplicate field name: {name!r}')
        seen.add(name)

    field_defaults = {}
    if defaults is not None:
        defaults = tuple(defaults)
        if len(defaults) > len(field_names):
            raise TypeError('Got more default values than field names')
        field_defaults = dict(reversed(list(zip(reversed(field_names),
                                                reversed(defaults)))))

    # Variables used in the methods and docstrings
    field_names = tuple(map(_sys.intern, field_names))
    num_fields = len(field_names)
    arg_list = repr(field_names).replace("'", "")[1:-1]
    repr_fmt = '(' + ', '.join(f'{name}=%r' for name in field_names) + ')'
    tuple_new = tuple.__new__
    _dict, _tuple, _len, _map, _zip = dict, tuple, len, map, zip

    # Create all the named tuple methods to be added to the class namespace

    s = f'def __new__(_cls, {arg_list}): return _tuple_new(_cls, ({arg_list}))'
    namespace = {'_tuple_new': tuple_new, '__name__': f'namedtuple_{typename}'}
    # Note: exec() has the side-effect of interning the field names
    exec(s, namespace)
    __new__ = namespace['__new__']
    __new__.__doc__ = f'Create new instance of {typename}({arg_list})'
    if defaults is not None:
        __new__.__defaults__ = defaults

    @classmethod
    def _make(cls, iterable):
        result = tuple_new(cls, iterable)
        if _len(result) != num_fields:
            raise TypeError(f'Expected {num_fields} arguments, got {len(result)}')
        return result

    _make.__func__.__doc__ = (f'Make a new {typename} object from a sequence '
                              'or iterable')

    def _replace(self,  **kwds):
        result = self._make(_map(kwds.pop, field_names, self))
        if kwds:
            raise ValueError(f'Got unexpected field names: {list(kwds)!r}')
        return result

    _replace.__doc__ = (f'Return a new {typename} object replacing specified '
                        'fields with new values')

    def __repr__(self):
        'Return a nicely formatted representation string'
        return self.__class__.__name__ + repr_fmt % self

    def _asdict(self):
        'Return a new dict which maps field names to their values.'
        return _dict(_zip(self._fields, self))

    def __getnewargs__(self):
        'Return self as a plain tuple.  Used by copy and pickle.'
        return _tuple(self)

    # Modify function metadata to help with introspection and debugging
    for method in (__new__, _make.__func__, _replace,
                   __repr__, _asdict, __getnewargs__):
        method.__qualname__ = f'{typename}.{method.__name__}'

    # Build-up the class namespace dictionary
    # and use type() to build the result class
    class_namespace = {
        '__doc__': f'{typename}({arg_list})',
        '__slots__': (),
        '_fields': field_names,
        '_field_defaults': field_defaults,
        # alternate spelling for backward compatibility
        '_fields_defaults': field_defaults,
        '__new__': __new__,
        '_make': _make,
        '_replace': _replace,
        '__repr__': __repr__,
        '_asdict': _asdict,
        '__getnewargs__': __getnewargs__,
    }
    for index, name in enumerate(field_names):
        doc = _sys.intern(f'Alias for field number {index}')
        class_namespace[name] = _tuplegetter(index, doc)

    result = type(typename, (tuple,), class_namespace)

    # For pickling to work, the __module__ variable needs to be set to the frame
    # where the named tuple is created.  Bypass this step in environments where
    # sys._getframe is not defined (Jython for example) or sys._getframe is not
    # defined for arguments greater than 0 (IronPython), or where the user has
    # specified a particular module.
    if module is None:
        try:
            module = _sys._getframe(1).f_globals.get('__name__', '__main__')
        except (AttributeError, ValueError):
            pass
    if module is not None:
        result.__module__ = module

    return result