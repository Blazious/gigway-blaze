import ipaddress
import socket
from urllib.parse import urlparse

import requests
from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import URLValidator


REQUEST_TIMEOUT_SECONDS = 4
USER_AGENT = 'GigWay-LinkVerifier/1.0'


def _normalise_url(url):
    value = str(url or '').strip()
    if not value:
        return ''
    if '://' not in value:
        value = f'https://{value}'
    return value


def _hostname_is_public(hostname):
    if not hostname:
        return False

    blocked_hosts = {'localhost', '127.0.0.1', '0.0.0.0', '::1'}
    if hostname.lower() in blocked_hosts:
        return False

    try:
        ip = ipaddress.ip_address(hostname)
        return not (
            ip.is_private or ip.is_loopback or ip.is_link_local
            or ip.is_reserved or ip.is_multicast or ip.is_unspecified
        )
    except ValueError:
        pass

    try:
        addresses = socket.getaddrinfo(hostname, None)
    except socket.gaierror:
        return False

    for address in addresses:
        ip = ipaddress.ip_address(address[4][0])
        if (
            ip.is_private or ip.is_loopback or ip.is_link_local
            or ip.is_reserved or ip.is_multicast or ip.is_unspecified
        ):
            return False
    return True


def _matches_allowed_domain(hostname, allowed_domains):
    if not allowed_domains:
        return True
    hostname = hostname.lower().removeprefix('www.')
    return any(
        hostname == domain or hostname.endswith(f'.{domain}')
        for domain in allowed_domains
    )


def validate_external_url(url, *, allowed_domains=None, label='URL'):
    """
    Return a normalized URL only when it is syntactically valid, public, and reachable.

    This is not identity verification. It proves the submitted proof link exists and
    belongs to the expected provider/domain, which prevents empty or dummy links from
    earning competency credit.
    """
    value = _normalise_url(url)
    if not value:
        return ''

    URLValidator(schemes=['https'])(value)
    parsed = urlparse(value)
    hostname = parsed.hostname

    if parsed.scheme != 'https':
        raise ValidationError(f'{label} must use HTTPS.')
    if not _matches_allowed_domain(hostname or '', allowed_domains):
        domains = ', '.join(sorted(allowed_domains or []))
        raise ValidationError(f'{label} must be from {domains}.')
    if not _hostname_is_public(hostname):
        raise ValidationError(f'{label} must point to a public website.')

    if not getattr(settings, 'VERIFY_EXTERNAL_LINKS', True):
        return value

    headers = {'User-Agent': USER_AGENT}
    try:
        response = requests.head(value, headers=headers, allow_redirects=True, timeout=REQUEST_TIMEOUT_SECONDS)
        if response.status_code in {405, 403}:
            response = requests.get(value, headers=headers, allow_redirects=True, timeout=REQUEST_TIMEOUT_SECONDS, stream=True)
    except requests.RequestException as exc:
        raise ValidationError(f'{label} could not be reached.') from exc

    if response.status_code >= 400:
        raise ValidationError(f'{label} does not appear to exist.')

    final_hostname = urlparse(response.url).hostname
    if not _matches_allowed_domain(final_hostname or '', allowed_domains):
        raise ValidationError(f'{label} redirects outside the allowed domain.')

    return value


def is_verified_external_url(url, *, allowed_domains=None):
    try:
        return bool(validate_external_url(url, allowed_domains=allowed_domains))
    except ValidationError:
        return False
