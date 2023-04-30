select * from GamesChoosed where timesPlayed = 1

update GamesChoosed set finished =0

select * from GamesChoosed where finished is null

select * from GamesChoosed order by lastTimePlayed desc

UPDATE GamesChoosed SET timesPlayed = timesPlayed + 1, lastTimePlayed = CURRENT_TIMESTAMP WHERE gameFolder = 'g:/jogos/ori and the blind forest - definitive edition'

