{% macro normalize_provider(column) %}
case lower(trim({{ column }}))
    when 'hsbc' then 'HSBC'
    when 'chase' then 'Chase'
    when 'bank of america' then 'Bank of America'
    when 'truist' then 'Truist'
    when 'us bancorp' then 'US Bancorp'
    when 'td bank' then 'TD Bank'
    when 'pnc bank' then 'PNC Bank'
    when 'capital one' then 'Capital One'
    when 'citibank' then 'Citibank'
    when 'wells fargo' then 'Wells Fargo'
    else initcap(trim({{ column }}))
end
{% endmacro %}
