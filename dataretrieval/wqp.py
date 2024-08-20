"""
Tool for downloading data from the Water Quality Portal (https://waterqualitydata.us)

See https://waterqualitydata.us/webservices_documentation for API reference

.. todo::

    - implement other services like Organization, Activity, etc.

"""
import warnings
from io import StringIO

import pandas as pd

from .utils import BaseMetadata, query

result_profiles_wqx3 = ['fullPhysChem', 'narrow', 'basicPhysChem']
result_profiles_legacy = ['resultPhysChem', 'biological',
                        'narrowResult']
activity_profiles_legacy = ['activityAll']
services_wqx3 = ['Result', 'Station', 'Activity']
services_legacy = ['Result', 'Station', 'Activity',
                   'Organization', 'Project',
                   'ProjectMonitoringLocationWeighting',
                   'ActivityMetric',
                   'ResultDetectionQuantitationLimit',
                   'BiologicalMetric']

def get_results(ssl_check=True, **kwargs):
    """Query the WQP for results.

    Any WQP API parameter can be passed as a keyword argument to this function.
    More information about the API can be found at:
    https://www.waterqualitydata.us/#advanced=true
    or the Swagger documentation at:
    https://www.waterqualitydata.us/data/swagger-ui/index.html?docExpansion=none&url=/data/v3/api-docs#/

    Parameters
    ----------
    ssl_check: bool
        If True, check the SSL certificate. Default is True. If False, SSL
        certificate is not checked.
    dataProfile: string
        Describes the type of columns to return with the result dataset.
        Most recent WQX3 profiles include 'fullPhysChem', 'narrow', and
        'basicPhysChem'. Legacy profiles include 'resultPhysChem',
        'biological', and 'narrowResult'. 
    siteid: string
        Concatenate an agency code, a hyphen ("-"), and a site-identification
        number.
    statecode: string
        Concatenate 'US', a colon (":"), and a FIPS numeric code
        (Example: Illinois is US:17)
    countycode: string
        A FIPS county code
    huc: string
        One or more eight-digit hydrologic units, delimited by semicolons.
    bBox: string
        Bounding box (Example: bBox=-92.8,44.2,-88.9,46.0)
    lat: string
        Latitude for radial search, expressed in decimal degrees, WGS84
    long: string
        Longitude for radial search
    within: string
        Distance for a radial search, expressed in decimal miles
    pCode: string
        One or more five-digit USGS parameter codes, separated by semicolons.
        NWIS only.
    startDateLo: string
        Date of earliest desired data-collection activity,
        expressed as 'MM-DD-YYYY'
    startDateHi: string
        Date of last desired data-collection activity,
        expressed as 'MM-DD-YYYY'
    characteristicName: string
        One or more case-sensitive characteristic names, separated by
        semicolons. (See https://www.waterqualitydata.us/public_srsnames/
        for available characteristic names)
    mimeType: string
        String specifying the output format which is 'csv' by default but can
        be 'geojson' 

    Returns
    -------
    df: ``pandas.DataFrame``
        Formatted data returned from the API query.
    md: :obj:`dataretrieval.utils.Metadata`
        Custom ``dataretrieval`` metadata object pertaining to the query.

    Examples
    --------
    .. code::

        >>> # Get results within a radial distance of a point
        >>> df, md = dataretrieval.wqp.get_results(
        ...     lat='44.2', long='-88.9', within='0.5'
        ... )

        >>> # Get results within a bounding box
        >>> df, md = dataretrieval.wqp.get_results(bBox='-92.8,44.2,-88.9,46.0')

    """

    kwargs = _alter_kwargs(kwargs)

    if 'dataProfile' not in kwargs:
        # set to wqx3 full result profile
        kwargs['dataProfile'] = 'fullPhysChem'
    # check to ensure profile is available in either legacy
    # or wqx3
    elif kwargs['dataProfile'] not in (result_profiles_legacy + result_profiles_wqx3):
        raise TypeError('dataProfile not recognized')
    
    # warn user when selecting a legacy profile
    if kwargs['dataProfile'] in result_profiles_legacy:
        _warn_legacy_use('dataProfile')
        url = wqp_url('Result')
    else:
        url = wqx3_url('Result')
    
    response = query(url, kwargs, delimiter=';', ssl_check=ssl_check)

    df = pd.read_csv(StringIO(response.text), delimiter=',')
    return df, WQP_Metadata(response)


def what_sites(ssl_check=True, **kwargs):
    """Search WQP for sites within a region with specific data.

    Any WQP API parameter can be passed as a keyword argument to this function.
    More information about the API can be found at:
    https://www.waterqualitydata.us/#advanced=true
    or the Swagger documentation at:
    https://www.waterqualitydata.us/data/swagger-ui/index.html?docExpansion=none&url=/data/v3/api-docs#/

    Parameters
    ----------
    ssl_check: bool
        If True, check the SSL certificate. Default is True. If False, SSL
        certificate is not checked.
    **kwargs: optional
        Accepts the same parameters as :obj:`dataretrieval.wqp.get_results`

    Returns
    -------
    df: ``pandas.DataFrame``
        Formatted data returned from the API query.
    md: :obj:`dataretrieval.utils.Metadata`
        Custom metadata object pertaining to the query.

    Examples
    --------
    .. code::

        >>> # Get sites within a radial distance of a point
        >>> df, md = dataretrieval.wqp.what_sites(
        ...     lat='44.2', long='-88.9', within='2.5'
        ... )

    """

    kwargs = _alter_kwargs(kwargs)

    url = wqx3_url('Station')
    response = query(url, payload=kwargs, delimiter=';', ssl_check=ssl_check)

    df = pd.read_csv(StringIO(response.text), delimiter=',')

    return df, WQP_Metadata(response)


def what_organizations(ssl_check=True, **kwargs):
    """Search WQP for organizations within a region with specific data.

    Any WQP API parameter can be passed as a keyword argument to this function.
    More information about the API can be found at:
    https://www.waterqualitydata.us/#advanced=true
    or the Swagger documentation at:
    https://www.waterqualitydata.us/data/swagger-ui/index.html?docExpansion=none&url=/data/v3/api-docs#/

    Parameters
    ----------
    ssl_check: bool
        If True, check the SSL certificate. Default is True. If False, SSL
        certificate is not checked.
    **kwargs: optional
        Accepts the same parameters as :obj:`dataretrieval.wqp.get_results`

    Returns
    -------
    df: ``pandas.DataFrame``
        Formatted data returned from the API query.
    md: :obj:`dataretrieval.utils.Metadata`
        Custom metadata object pertaining to the query.

    Examples
    --------
    .. code::

        >>> # Get all organizations in the WQP
        >>> df, md = dataretrieval.wqp.what_organizations()

    """

    _warn_legacy_use('service')

    kwargs = _alter_kwargs(kwargs)

    url = wqp_url('Organization')
    response = query(url, payload=kwargs, delimiter=';', ssl_check=ssl_check)

    df = pd.read_csv(StringIO(response.text), delimiter=',')

    return df, WQP_Metadata(response)


def what_projects(ssl_check=True, **kwargs):
    """Search WQP for projects within a region with specific data.

    Any WQP API parameter can be passed as a keyword argument to this function.
    More information about the API can be found at:
    https://www.waterqualitydata.us/#advanced=true
    or the Swagger documentation at:
    https://www.waterqualitydata.us/data/swagger-ui/index.html?docExpansion=none&url=/data/v3/api-docs#/

    Parameters
    ----------
    ssl_check: bool
        If True, check the SSL certificate. Default is True. If False, SSL
        certificate is not checked.
    **kwargs: optional
        Accepts the same parameters as :obj:`dataretrieval.wqp.get_results`

    Returns
    -------
    df: ``pandas.DataFrame``
        Formatted data returned from the API query.
    md: :obj:`dataretrieval.utils.Metadata`
        Custom metadata object pertaining to the query.

    Examples
    --------
    .. code::

        >>> # Get projects within a HUC region
        >>> df, md = dataretrieval.wqp.what_projects(huc='19')

    """
    _warn_legacy_use('service')

    kwargs = _alter_kwargs(kwargs)

    url = wqp_url('Project')
    response = query(url, payload=kwargs, delimiter=';', ssl_check=ssl_check)

    df = pd.read_csv(StringIO(response.text), delimiter=',')

    return df, WQP_Metadata(response)


def what_activities(ssl_check=True, **kwargs):
    """Search WQP for activities within a region with specific data.

    Any WQP API parameter can be passed as a keyword argument to this function.
    More information about the API can be found at:
    https://www.waterqualitydata.us/#advanced=true
    or the Swagger documentation at:
    https://www.waterqualitydata.us/data/swagger-ui/index.html?docExpansion=none&url=/data/v3/api-docs#/

    Parameters
    ----------
    ssl_check: bool
        If True, check the SSL certificate. Default is True. If False, SSL
        certificate is not checked.
    dataProfile: string
        Describes the type of columns to return with the result dataset.
        Currently, only the legacy services have a single data profile:
        'activityAll'. 
    **kwargs: optional
        Accepts the same parameters as :obj:`dataretrieval.wqp.get_results`

    Returns
    -------
    df: ``pandas.DataFrame``
        Formatted data returned from the API query.
    md: :obj:`dataretrieval.utils.Metadata`
        Custom metadata object pertaining to the query.

    Examples
    --------
    .. code::

        >>> # Get activities within Washington D.C.
        >>> # during a specific time period
        >>> df, md = dataretrieval.wqp.what_activities(
        ...     statecode='US:11', startDateLo='12-30-2019', startDateHi='01-01-2020'
        ... )

    """

    kwargs = _alter_kwargs(kwargs)

    if 'dataProfile' not in kwargs:
        url = wqx3_url('Activity')
    elif kwargs['dataProfile'] not in activity_profiles_legacy:
        raise TypeError('dataProfile not recognized')
    else:
        _warn_legacy_use('service')
        url = wqp_url('Activity')
        
    
    response = query(url, payload=kwargs, delimiter=';', ssl_check=ssl_check)

    df = pd.read_csv(StringIO(response.text), delimiter=',')

    return df, WQP_Metadata(response)


def what_detection_limits(ssl_check=True, **kwargs):
    """Search WQP for result detection limits within a region with specific
    data.

    Any WQP API parameter can be passed as a keyword argument to this function.
    More information about the API can be found at:
    https://www.waterqualitydata.us/#advanced=true
    or the Swagger documentation at:
    https://www.waterqualitydata.us/data/swagger-ui/index.html?docExpansion=none&url=/data/v3/api-docs#/

    Parameters
    ----------
    ssl_check: bool
        If True, check the SSL certificate. Default is True. If False, SSL
        certificate is not checked.
    **kwargs: optional
        Accepts the same parameters as :obj:`dataretrieval.wqp.get_results`

    Returns
    -------
    df: ``pandas.DataFrame``
        Formatted data returned from the API query.
    md: :obj:`dataretrieval.utils.Metadata`
        Custom metadata object pertaining to the query.

    Examples
    --------
    .. code::

        >>> # Get detection limits for Nitrite measurements in Rhode Island
        >>> # between specific dates
        >>> df, md = dataretrieval.wqp.what_detection_limits(
        ...     statecode='US:44',
        ...     characteristicName='Nitrite',
        ...     startDateLo='01-01-2021',
        ...     startDateHi='02-20-2021',
        ... )

    """
    _warn_legacy_use('service')

    kwargs = _alter_kwargs(kwargs)

    url = wqp_url('ResultDetectionQuantitationLimit')
    response = query(url, payload=kwargs, delimiter=';', ssl_check=ssl_check)

    df = pd.read_csv(StringIO(response.text), delimiter=',')

    return df, WQP_Metadata(response)


def what_habitat_metrics(ssl_check=True, **kwargs):
    """Search WQP for habitat metrics within a region with specific data.

    Any WQP API parameter can be passed as a keyword argument to this function.
    More information about the API can be found at:
    https://www.waterqualitydata.us/#advanced=true
    or the Swagger documentation at:
    https://www.waterqualitydata.us/data/swagger-ui/index.html?docExpansion=none&url=/data/v3/api-docs#/

    Parameters
    ----------
    ssl_check: bool
        If True, check the SSL certificate. Default is True. If False, SSL
        certificate is not checked.
    **kwargs: optional
        Accepts the same parameters as :obj:`dataretrieval.wqp.get_results`

    Returns
    -------
    df: ``pandas.DataFrame``
        Formatted data returned from the API query.
    md: :obj:`dataretrieval.utils.Metadata`
        Custom metadata object pertaining to the query.

    Examples
    --------
    .. code::

        >>> # Get habitat metrics for a state (Rhode Island in this case)
        >>> df, md = dataretrieval.wqp.what_habitat_metrics(statecode='US:44')

    """
    _warn_legacy_use('service')

    kwargs = _alter_kwargs(kwargs)

    url = wqp_url('BiologicalMetric')
    response = query(url, payload=kwargs, delimiter=';', ssl_check=ssl_check)

    df = pd.read_csv(StringIO(response.text), delimiter=',')

    return df, WQP_Metadata(response)


def what_project_weights(ssl_check=True, **kwargs):
    """Search WQP for project weights within a region with specific data.

    Any WQP API parameter can be passed as a keyword argument to this function.
    More information about the API can be found at:
    https://www.waterqualitydata.us/#advanced=true
    or the Swagger documentation at:
    https://www.waterqualitydata.us/data/swagger-ui/index.html?docExpansion=none&url=/data/v3/api-docs#/

    Parameters
    ----------
    ssl_check: bool
        If True, check the SSL certificate. Default is True. If False, SSL
        certificate is not checked.
    **kwargs: optional
        Accepts the same parameters as :obj:`dataretrieval.wqp.get_results`

    Returns
    -------
    df: ``pandas.DataFrame``
        Formatted data returned from the API query.
    md: :obj:`dataretrieval.utils.Metadata`
        Custom metadata object pertaining to the query.

    Examples
    --------
    .. code::

        >>> # Get project weights for a state (North Dakota in this case)
        >>> # within a set time period
        >>> df, md = dataretrieval.wqp.what_project_weights(
        ...     statecode='US:38', startDateLo='01-01-2006', startDateHi='01-01-2009'
        ... )

    """
    _warn_legacy_use('service')

    kwargs = _alter_kwargs(kwargs)

    url = wqp_url('ProjectMonitoringLocationWeighting')
    response = query(url, payload=kwargs, delimiter=';', ssl_check=ssl_check)

    df = pd.read_csv(StringIO(response.text), delimiter=',')

    return df, WQP_Metadata(response)


def what_activity_metrics(ssl_check=True, **kwargs):
    """Search WQP for activity metrics within a region with specific data.

    Any WQP API parameter can be passed as a keyword argument to this function.
    More information about the API can be found at:
    https://www.waterqualitydata.us/#advanced=true
    or the Swagger documentation at:
    https://www.waterqualitydata.us/data/swagger-ui/index.html?docExpansion=none&url=/data/v3/api-docs#/

    Parameters
    ----------
    ssl_check: bool
        If True, check the SSL certificate. Default is True. If False, SSL
        certificate is not checked.
    **kwargs: optional
        Accepts the same parameters as :obj:`dataretrieval.wqp.get_results`

    Returns
    -------
    df: ``pandas.DataFrame``
        Formatted data returned from the API query.
    md: :obj:`dataretrieval.utils.Metadata`
        Custom metadata object pertaining to the query.

    Examples
    --------
    .. code::

        >>> # Get activity metrics for a state (North Dakota in this case)
        >>> # within a set time period
        >>> df, md = dataretrieval.wqp.what_activity_metrics(
        ...     statecode='US:38', startDateLo='07-01-2006', startDateHi='12-01-2006'
        ... )

    """
    _warn_legacy_use('service')

    kwargs = _alter_kwargs(kwargs)

    url = wqp_url('ActivityMetric')
    response = query(url, payload=kwargs, delimiter=';', ssl_check=ssl_check)

    df = pd.read_csv(StringIO(response.text), delimiter=',')

    return df, WQP_Metadata(response)


def wqp_url(service):
    """Construct the WQP URL for a given service."""
    if service not in services_legacy:
        raise TypeError('Legacy service not recognized')
    base_url = 'https://www.waterqualitydata.us/data/'
    return f'{base_url}{service}/Search?'

def wqx3_url(service):
    """Construct the WQP URL for a given WQX 3.0 service."""
    if service not in services_wqx3:
        raise TypeError('WQX3 service not recognized')
    base_url = 'https://www.waterqualitydata.us/wqx3/'
    return f'{base_url}{service}/search?'


class WQP_Metadata(BaseMetadata):
    """Metadata class for WQP service, derived from BaseMetadata.

    Attributes
    ----------
    url : str
        Response url
    query_time: datetme.timedelta
        Response elapsed time
    header: requests.structures.CaseInsensitiveDict
        Response headers
    comments: None
        Metadata comments. WQP does not return comments.
    site_info: tuple[pd.DataFrame, NWIS_Metadata] | None
        Site information if the query included `sites`, `site` or `site_no`.
    """

    def __init__(self, response, **parameters) -> None:
        """Generates a standard set of metadata informed by the response with specific
        metadata for WQP data.

        Parameters
        ----------
        response: Response
            Response object from requests module

        parameters: unpacked dictionary
            Unpacked dictionary of the parameters supplied in the request

        Returns
        -------
        md: :obj:`dataretrieval.wqp.WQP_Metadata`
            A ``dataretrieval`` custom :obj:`dataretrieval.wqp.WQP_Metadata` object.

        """

        super().__init__(response)

        self._parameters = parameters

        @property
        def site_info(self):
            if 'sites' in self._parameters:
                return what_sites(sites=parameters['sites'])
            elif 'site' in self._parameters:
                return what_sites(sites=parameters['site'])
            elif 'site_no' in self._parameters:
                return what_sites(sites=parameters['site_no'])


def _alter_kwargs(kwargs):
    """Private function to manipulate **kwargs.

    Not all query parameters are currently supported by ``dataretrieval``,
    so this function is used to set some of them and raise warnings to the
    user so they are aware of which are being hard-set.

    """

    if kwargs.get('mimeType', 'csv') == 'geojson':
        warnings.warn('GeoJSON not yet supported, mimeType set to csv.')
    kwargs['mimeType'] = 'csv'

    return kwargs


def _warn_v3_profiles_outage():
    """Private function for warning message about WQX 3.0 profiles
    """

    warnings.warn(
        'USGS discrete water quality data availability '
        'and format are changing. Beginning in March 2024 '
        'the data obtained from legacy profiles will not '
        'include new USGS data or recent updates to existing '
        'data. To view the status of changes in data '
        'availability and code functionality, visit: '
        'https://doi-usgs.github.io/dataRetrieval/articles/Status.html. '
        'If you have additional questions about these changes, '
        'email CompTools@usgs.gov.'
    )

def _warn_legacy_use(type):
    """Private function for warning message about using legacy profiles
    or services
    """

    warnings.warn(
        f'The {type} you have selected is currently only '
        'available in the legacy Water Quality Portal '
        'profiles. This means that any USGS data served '
        'are stale as of March 2024. Please review the '
        f'updated WQX3.0 {type}s in the dataretrieval-python '
        'documentation.'
    )
