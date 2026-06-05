from pydantic import BaseModel, ConfigDict


class CheckItemOut(BaseModel):
    id: int
    equipment_type: str
    item_code: str
    item_name: str
    input_type: str
    standard_value: str | None = None
    unit: str | None = None
    required: int
    sort_order: int

    model_config = ConfigDict(from_attributes=True)
