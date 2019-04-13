from setout import setout

if __name__ == '__main__':

    passed = 0
    failed = 0

    def check(spec, args, expected):
        out = setout(spec, *args)
        if out != expected:
            global failed
            failed += 1
            print('FAIL: setout("{}", {}) returned "{}" expected "{}"'.format(spec, args, out, expected))
        else:
            global passed
            passed += 1
            print('PASS: setout("{}", {})'.format(spec, args))

    check('~&Hello', [], 'Hello')
    check('~%Hello', [], '\nHello')
    check('~:d', [1234567], '1,234,567')
    check("~,,'.,4:d", [1234567], '123.4567')
    check("~2,'0d", [3], '03')
    check("~4,'0d-~2,'0d-~2,'0d", [2018, 6, 5], '2018-06-05')
    check("~10d", [123], "       123")
    check("~:d", [1000000], "1,000,000")
    check("~b", [100], "1100100")
    check("~b", [12341234213], "1011011111100110000100101000100101")
    check("~,,' ,4:b", [12341234213], "10 1101 1111 1001 1000 0100 1010 0010 0101")
    check("~o", [1234], "2322")
    check("~x", [0xcafebabe], "cafebabe")
    check("~:@(~x~)", [0xcafebabe], "CAFEBABE")
    check('~a', [10], '10')
    check('~10a', [10], '10        ')
    check('~10@a', [10], '        10')
    check('~s', [10], '10')
    check('~10s', [10], '10        ')
    check('~10@s', [10], '        10')
    check('~(~a~)', ['The quick brown fox'], 'the quick brown fox')
    check('~:(~a~)', ['The quick brown fox'], 'The Quick Brown Fox')
    check('~@(~a~)', ['The quick brown fox'], 'The quick brown fox')
    check('~:@(~a~)', ['The quick brown fox'], 'THE QUICK BROWN FOX')
    check("pig~p", [1], "pig")
    check("pig~p", [10], "pigs")
    check("~d pig~:p", [1], "1 pig")
    check("~d pig~:p", [10], "10 pigs")
    check("~d ~d ~d ~@*~d ~d ~d", [1, 2, 3], "1 2 3 1 2 3")
    check("~d ~d ~d ~:*~d", [1, 2, 3], "1 2 3 3")
    check("~d ~*~d", [1, 2, 3], "1 3")
    check("~[Siamese~;Manx~;Persian~] Cat", [0], "Siamese Cat")
    check("~[Siamese~;Manx~;Persian~] Cat", [1], "Manx Cat")
    check("~[Siamese~;Manx~;Persian~] Cat", [2], "Persian Cat")
    check("~[Siamese~;Manx~;Persian~:;Alley~] Cat", [2], "Persian Cat")
    check("~[Siamese~;Manx~;Persian~:;Alley~] Cat", [3], "Alley Cat")
    check("~[Siamese~;Manx~;Persian~:;Alley~] Cat", [5], "Alley Cat")
    check("~[Siamese~;Manx~;Persian~:;Alley~] Cat", [100], "Alley Cat")
    check("~:[No~;Yes~]", [True], "Yes")
    check("~:[No~;Yes~]", [False], "No")
    check("~@[truthy value ~a~]", [100], "truthy value 100")
    check("~@[truthy value ~a~]", [False], "")
    check("~@[truthy value ~a~]", [None], "")
    check("~{~a ~}", [[1, 2, 3]], "1 2 3 ")
    check("~{~}", ["~a ", [1, 2, 3]], "1 2 3 ")
    check("~{<~a, ~a> ~}", [[1, 2, 3, 4]], "<1, 2> <3, 4> ")
    check("~1{~a ~}", [[1, 2, 3]], "1 ")
    check("~2{~a ~}", [[1, 2, 3]], "1 2 ")
    check("~{~a~^~}", [[1, 2, 3]], "123")
    check("~{~a~^ ~}", [[1, 2, 3]], "1 2 3")
    check("~:{<~a, ~a> ~}", [[[1, 2], [3, 4, 5, 6]]], "<1, 2> <3, 4> ")
    check("~:{<~a~^> ~}", [[[1, 2], [3, 4, 5, 6]]], "<1> <3> ")

    print(setout("~&~:[Uh oh.~;All Okay!~] ~:d passed; ~:d failed~%", failed == 0, passed, failed))
