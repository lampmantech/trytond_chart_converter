# morons put commas in CSV fields!
s@,"\([^",]*\),\([^",]*\)",@,"\1 \2",@g
# morons put ampersands in fields destined for XML!
s@[&]@and@g
s@[""]@@g
s@FALSE@False@
s@TRUE@True@
