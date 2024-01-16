from typing import TypedDict, TYPE_CHECKING, Optional, Union

if TYPE_CHECKING:
    from typing import NotRequired


class CustomGraphData(TypedDict):
    type: str
    value1: NotRequired[Optional[Union[int, str]]]
    value2: NotRequired[Optional[Union[int, str]]]
    value3: NotRequired[Optional[Union[int, str]]]
