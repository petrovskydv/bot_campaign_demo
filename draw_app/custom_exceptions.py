
class QrCodeNoDataError(Exception):
    pass


class QrCodeNotValidError(Exception):
    pass


class QualitySettingNotFilled(Exception):
    pass


class FnsQRError(Exception):
    pass


class FnsNoDataYetError(Exception):
    pass


class FnsGetTemporaryTokenError(Exception):
    pass


class FnsNotAvailable(Exception):
    pass


class FnsCashboxCompleteError(Exception):
    pass


class FnsInternalError(Exception):
    pass


class FnsProcessing(Exception):
    pass
