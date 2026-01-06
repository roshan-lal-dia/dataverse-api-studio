"""
Query Builder - Generates OData and FetchXML queries
"""

from typing import List, Dict, Optional, Any
from dataclasses import dataclass
from enum import Enum


class FilterOperator(Enum):
    """Supported filter operators"""
    EQUAL = "eq"
    NOT_EQUAL = "ne"
    GREATER_THAN = "gt"
    GREATER_EQUAL = "ge"
    LESS_THAN = "lt"
    LESS_EQUAL = "le"
    CONTAINS = "contains"
    STARTS_WITH = "startswith"
    ENDS_WITH = "endswith"
    IN = "in"
    NOT_IN = "not in"


class LogicalOperator(Enum):
    """Logical operators for combining filters"""
    AND = "and"
    OR = "or"


@dataclass
class FilterCondition:
    """A single filter condition"""
    field: str
    operator: FilterOperator
    value: Any
    
    def to_odata(self) -> str:
        """Convert to OData filter syntax"""
        # Handle string values (need quotes)
        if isinstance(self.value, str):
            value_str = f"'{self.value}'"
        elif isinstance(self.value, bool):
            value_str = "true" if self.value else "false"
        elif self.value is None:
            value_str = "null"
        else:
            value_str = str(self.value)
        
        # Handle function operators
        if self.operator in [FilterOperator.CONTAINS, FilterOperator.STARTS_WITH, FilterOperator.ENDS_WITH]:
            return f"{self.operator.value}({self.field}, {value_str})"
        elif self.operator == FilterOperator.IN:
            # Convert list to comma-separated
            if isinstance(self.value, list):
                values = ",".join([f"'{v}'" if isinstance(v, str) else str(v) for v in self.value])
                return f"{self.field} in ({values})"
        
        # Standard binary operators
        return f"{self.field} {self.operator.value} {value_str}"


@dataclass
class FilterGroup:
    """A group of filters combined with logical operator"""
    operator: LogicalOperator
    conditions: List[Any]  # Can be FilterCondition or FilterGroup
    
    def to_odata(self) -> str:
        """Convert to OData filter syntax"""
        parts = []
        
        for condition in self.conditions:
            if isinstance(condition, FilterCondition):
                parts.append(condition.to_odata())
            elif isinstance(condition, FilterGroup):
                parts.append(f"({condition.to_odata()})")
        
        connector = f" {self.operator.value} "
        return connector.join(parts)


class QueryBuilder:
    """Build OData and FetchXML queries"""
    
    def __init__(self, entity_name: str, entity_set_name: Optional[str] = None):
        """
        Initialize query builder for an entity
        Args:
            entity_name: Logical name of the entity (e.g., 'account')
            entity_set_name: Collection name from metadata (e.g., 'accounts', 'opportunities')
                           If not provided, defaults to entity_name + 's'
        """
        self.entity_name = entity_name
        self.entity_set_name = entity_set_name or f"{entity_name}s"
        self.select_fields: List[str] = []
        self.filter_group: Optional[FilterGroup] = None
        self.order_by: List[tuple] = []  # (field, direction)
        self.top: Optional[int] = None
        self.expand: List[Dict] = []  # For related entities
    
    def select(self, *fields: str) -> 'QueryBuilder':
        """Add fields to select"""
        self.select_fields.extend(fields)
        return self
    
    def filter(self, filter_group: FilterGroup) -> 'QueryBuilder':
        """Set filter group"""
        self.filter_group = filter_group
        return self
    
    def order(self, field: str, direction: str = "asc") -> 'QueryBuilder':
        """Add ordering"""
        self.order_by.append((field, direction))
        return self
    
    def limit(self, count: int) -> 'QueryBuilder':
        """Set top limit"""
        self.top = count
        return self
    
    def expand_related(self, nav_property: str, select: Optional[List[str]] = None) -> 'QueryBuilder':
        """Expand related entity"""
        self.expand.append({
            "property": nav_property,
            "select": select or []
        })
        return self
    
    def to_odata(self) -> str:
        """Generate OData query string"""
        parts = []
        
        # $select
        if self.select_fields:
            parts.append(f"$select={','.join(self.select_fields)}")
        
        # $filter
        if self.filter_group:
            filter_str = self.filter_group.to_odata()
            parts.append(f"$filter={filter_str}")
        
        # $orderby
        if self.order_by:
            order_parts = [f"{field} {direction}" for field, direction in self.order_by]
            parts.append(f"$orderby={','.join(order_parts)}")
        
        # $top
        if self.top:
            parts.append(f"$top={self.top}")
        
        # $expand
        if self.expand:
            expand_parts = []
            for exp in self.expand:
                nav_prop = exp["property"]
                if exp["select"]:
                    expand_parts.append(f"{nav_prop}($select={','.join(exp['select'])})")
                else:
                    expand_parts.append(nav_prop)
            parts.append(f"$expand={','.join(expand_parts)}")
        
        return "&".join(parts)
    
    def to_fetchxml(self) -> str:
        """Generate FetchXML query"""
        lines = ['<fetch>']
        
        # Entity element
        entity_attrs = [f'name="{self.entity_name}"']
        if self.top:
            entity_attrs.append(f'top="{self.top}"')
        
        lines.append(f'  <entity {" ".join(entity_attrs)}>')
        
        # Attributes (select)
        if self.select_fields:
            for field in self.select_fields:
                lines.append(f'    <attribute name="{field}" />')
        else:
            lines.append('    <all-attributes />')
        
        # Orders
        for field, direction in self.order_by:
            desc = 'true' if direction.lower() == 'desc' else 'false'
            lines.append(f'    <order attribute="{field}" descending="{desc}" />')
        
        # Filters
        if self.filter_group:
            filter_xml = self._filter_group_to_fetchxml(self.filter_group, indent=4)
            lines.append(filter_xml)
        
        # Link entities (expand)
        for exp in self.expand:
            nav_prop = exp["property"]
            lines.append(f'    <link-entity name="{nav_prop}" from="..." to="..." alias="{nav_prop}">')
            
            if exp["select"]:
                for field in exp["select"]:
                    lines.append(f'      <attribute name="{field}" />')
            
            lines.append('    </link-entity>')
        
        lines.append('  </entity>')
        lines.append('</fetch>')
        
        return '\n'.join(lines)
    
    def _filter_group_to_fetchxml(self, group: FilterGroup, indent: int = 0) -> str:
        """Convert filter group to FetchXML"""
        spaces = ' ' * indent
        lines = [f'{spaces}<filter type="{group.operator.value}">']
        
        for condition in group.conditions:
            if isinstance(condition, FilterCondition):
                cond_xml = self._filter_condition_to_fetchxml(condition, indent + 2)
                lines.append(cond_xml)
            elif isinstance(condition, FilterGroup):
                nested_xml = self._filter_group_to_fetchxml(condition, indent + 2)
                lines.append(nested_xml)
        
        lines.append(f'{spaces}</filter>')
        return '\n'.join(lines)
    
    def _filter_condition_to_fetchxml(self, condition: FilterCondition, indent: int = 0) -> str:
        """Convert filter condition to FetchXML"""
        spaces = ' ' * indent
        
        # Map OData operators to FetchXML
        operator_map = {
            FilterOperator.EQUAL: "eq",
            FilterOperator.NOT_EQUAL: "ne",
            FilterOperator.GREATER_THAN: "gt",
            FilterOperator.GREATER_EQUAL: "ge",
            FilterOperator.LESS_THAN: "lt",
            FilterOperator.LESS_EQUAL: "le",
            FilterOperator.CONTAINS: "like",
            FilterOperator.STARTS_WITH: "begins-with",
            FilterOperator.ENDS_WITH: "ends-with",
            FilterOperator.IN: "in",
        }
        
        operator = operator_map.get(condition.operator, condition.operator.value)
        
        # Handle LIKE operator (add wildcards)
        value = condition.value
        if condition.operator == FilterOperator.CONTAINS:
            value = f"%{value}%"
        
        return f'{spaces}<condition attribute="{condition.field}" operator="{operator}" value="{value}" />'
    
    def get_url(self, base_url: str) -> str:
        """
        Get full query URL using EntitySetName from metadata
        """
        query_string = self.to_odata()
        
        if query_string:
            return f"{base_url}/api/data/v9.2/{self.entity_set_name}?{query_string}"
        else:
            return f"{base_url}/api/data/v9.2/{self.entity_set_name}"


# Helper functions for common query patterns
def create_simple_query(entity: str, filters: Dict[str, Any], select: Optional[List[str]] = None) -> QueryBuilder:
    """Create a simple query with AND filters"""
    builder = QueryBuilder(entity)
    
    if select:
        builder.select(*select)
    
    if filters:
        conditions = [
            FilterCondition(field, FilterOperator.EQUAL, value)
            for field, value in filters.items()
        ]
        filter_group = FilterGroup(LogicalOperator.AND, conditions)
        builder.filter(filter_group)
    
    return builder
