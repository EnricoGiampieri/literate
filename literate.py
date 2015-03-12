# -*- coding: utf-8 -*-
"""
Created on Tue Feb 10 20:34:09 2015

@author: enrico.giampieri2
"""

# %%
import itertools as it
import tokenize
from io import StringIO, BytesIO
from itertools import groupby
from contextlib import contextmanager
import sys
from docutils.core import publish_parts
import os


# %%
# this wrap the show function and keeps track of the last created plot
class MyPylabShow(object):
    def __init__(self):
        self.fig_index = []
        self.last_drawn = []

    def __call__(self, *args, **kwargs):
        import pylab
        self.last_drawn = []
        # figs = list(map(pylab.figure, pylab.get_fignums()))
        fig = pylab.gcf()
        file_descriptor = BytesIO()
        fig.savefig(file_descriptor, format='png')
        self.last_drawn.append(file_descriptor)

    def pop(self):
        res = self.last_drawn
        self.last_drawn = []
        return res

    # the output cage: it captures stdout, stderr and pylab figures temporarely
    @contextmanager
    def redifine_output(self, glob):
        """intercept the output to stdout, stderr and the pylab shows
        """
        old_stdout = sys.stdout
        my_stdout = StringIO()
        sys.stdout = my_stdout
        old_stderr = sys.stderr
        my_stderr = StringIO()
        sys.stderr = my_stderr

        pylab_name = "__pylab__literate__"
        exec("import pylab as {}\n".format(pylab_name), glob)
        old_pylab_show = glob[pylab_name].show
        old_figure_show = glob[pylab_name].Figure.show
        old_pyplot_show = glob[pylab_name].matplotlib.pyplot.show

        replaced = {}
        glob[pylab_name].show = self
        glob[pylab_name].Figure.show = self
        glob[pylab_name].matplotlib.pyplot.show = self
        try:
            yield my_stdout, my_stderr
        finally:
            sys.stdout = old_stdout
            sys.stderr = old_stderr
            glob[pylab_name].show = old_pylab_show
            glob[pylab_name].Figure.show = old_figure_show
            glob[pylab_name].matplotlib.pyplot.show = old_pyplot_show
            for name, value in replaced.items():
                glob[name] = value


# %%
# DEDENT and INDENT are at the beginning of the line, but maybe after comments
def _evaluate_indent_variation(token_seq, **kwargs):
    up = sum(token.type == tokenize.INDENT for token in token_seq)
    down = sum(token.type == tokenize.DEDENT for token in token_seq)
    return up-down

def _is_continued_block(token_line):
    """this recognize if the block is an else or similar, that follow
    another block even if it is on the same line.

    This should be a separate function at a certain point...
    """
    for token in token_line:
        if token.type in [tokenize.INDENT,
                          tokenize.DEDENT,
                          tokenize.COMMENT,
                          tokenize.NEWLINE,
                          tokenize.NL,
                          tokenize.ENCODING,
                          tokenize.ENDMARKER,
                          ]:
            continue
        elif token.type == tokenize.NAME:
            name = token.string
            if name in ['elif', 'else', 'except', 'finally']:
                return True
            else:
                return False
        else:
            return False
    return False

# %%

class CodeGroup(object):
    """this is the main class, responsible for holding the code
    and executing it
    """

    def __init__(self, block_lines, previous_block=None):
        """the input should be a list of lists of tokens

        ech list is a logical line"""
        self.lines = block_lines
        self.previous = previous_block
        self.following = None
        if self.previous is not None:
            self.previous.following = self
        self.results = {}
        self.globals = None

    def get_index(self):
        if self.previous is None:
            return 0
        else:
            return 1+self.previous.get_index()

    def __str__(self):
        is_whiteline = lambda s: s == '\\'
        groups_lines = tokenize.untokenize(self.lines)
        # remove the superfluous lines at the beginning due
        # to how untokenize work join them together again
        groups_lines = it.dropwhile(is_whiteline, groups_lines.split('\n'))
        groups_lines = list(groups_lines)
        # this final bit is required to assure that the combination
        # of the various groups reconstruct the original source code
        if groups_lines[0] == '\n':
            groups_lines = groups_lines[1:]
        return "\n".join(groups_lines)

    def set_mpl_agg(self):
        if not self.globals:
            exec('__name__ = "__main__"', self.globals)
            exec("import matplotlib as __mpl__literate__\n", self.globals)
            exec("__mpl__literate__.use('Agg')\n", self.globals)
            exec("del __mpl__literate__", self.globals)

    def execute(self, global_dict, pylab_show_cage):
        assert type(global_dict) == dict, "the globals should be a base dict!"
        self.globals = global_dict
        myshow = pylab_show_cage
        # this is necessary to allow me to keep writing even in the output cage
        self.set_mpl_agg()
        with myshow.redifine_output(global_dict) as out_err:
            # try to capture possible exceptions generated by the code
            # to save them. This could lead to capture external exceptions
            # and save them as results, but I can't see any way out of this
            exceptions = None
            try:
                exec(str(self), global_dict)
            # TODO: this is not really giving me the information I want,
            # TODO: search a better method
            except Exception as e:
                # if isinstance(e, KeyboardInterrupt):
                raise e
                # exc_type, exc_value, exc_traceback = sys.exc_info()
                # exceptions = e
            # take the output results out of the output cage
            out = out_err[0].getvalue()
            err = out_err[1].getvalue()

            figures = myshow.pop()

            # output to normal lines the global keys, just a debug thing
            # create the result block with the code and all the results
            # and append it to the total array of results
            # each block execution results should be saved in here.
            # it contains the code text, the output, the figures filenames
            # and possible errors
            self.results = {'standard output': out,
                            "standard error": err,
                            "generated figures": figures,
                            "exceptions generated": exceptions,
                            }
        return self.results

    def has_results(self):
        if not self.results:
            return False
        for key, value in self.results.items():
            if value:
                return True
        return False

    def is_docstring(self):
        """consider a docstring a string isolated from the rest
        without lines of codes around, but possible with comments.
        return the content or an empty string if invalid.
        if the string is empty, it will not consider it as valid
        """
        is_string = True
        content = ""
        for token in self.lines:
            if token.type not in [tokenize.INDENT,
                                  tokenize.DEDENT,
                                  tokenize.COMMENT,
                                  tokenize.STRING,
                                  tokenize.NEWLINE,
                                  tokenize.NL,
                                  tokenize.ENCODING,
                                  tokenize.ENDMARKER,
                                  ]:
                is_string = False
                break
            elif token.type == tokenize.STRING:
                content += eval(token.string)
        return content if is_string else ""

    def compile(self, output_dir):
        """compile the executed code into rst
        """
        content = self.is_docstring()
        if content:
            return content

        compiled_rst = ".. code:: python\n\n"
        indented_lines = ["    "+line for line in str(self).split('\n')]
        compiled_rst += "\n".join(indented_lines)

        if self.has_results():
            compiled_rst += '\n\n'

        if "standard error" in self.results:
            if self.results["standard error"]:
                compiled_rst += ".. warning::\n\n"
                for line in self.results["standard error"].split('\n'):
                    compiled_rst += "    "+line+'\n'
        if "exceptions generated" in self.results:
            if self.results["exceptions generated"]:
                compiled_rst += ".. warning:: Exception Raised\n\n"
                generated = str(self.results["exceptions generated"])
                for line in generated.split('\n'):
                    compiled_rst += "    "+line+'\n'
        if "standard output" in self.results:
            if self.results["standard output"]:
                compiled_rst += "::\n\n"
                for line in self.results["standard output"].split('\n'):
                    compiled_rst += "    "+line+'\n'
        if "generated figures" in self.results:
            for figure_bytes in self.results["generated figures"]:
                index = self.get_index()
                f_name = output_dir+"figure_{}.png".format(index)
                with open(f_name, 'wb') as file:
                    file.write(figure_bytes.getvalue())

                compiled_rst += ".. image:: "+str(f_name)+"\n"
        return compiled_rst

    @staticmethod
    def _iterate_input_logical_lines(readline):
        # split the lines in tokens
        tokens = list(tokenize.generate_tokens(readline))
        # NEWLINE is the interruption of a logical line
        # NL is the end of a physical line withuot ending the logical one
        is_complete_line = lambda token: token.type == tokenize.NEWLINE
        res = list(list(l[1]) for l in groupby(tokens, is_complete_line))
        # these are the logical lines, ending with an NL
        lines = [i0+i1 for i0, i1 in zip(res[::2], res[1::2])]
        # for each line, determins its level of variation of indentation
        var_indent_lev = map(_evaluate_indent_variation, lines)
        # accumulate to obtain the total one
        indent_levels = it.accumulate(var_indent_lev)
        for line, indent_level in zip(lines, indent_levels):
            yield line, indent_level

    @classmethod
    def _iterate_groups(group_cls, lines):
        is_decorator = lambda lg: lg[-1].line.strip().startswith('@')
        last_group = []
        last_created_group = None
        for line, indent_level in lines:
            # if is a flat line, either start or if it is a decorator
            # store it for later
            if indent_level == 0:
                # have to check for decorators
                if (not last_group) or is_decorator(last_group):
                    last_group.extend(line)
                # now I check if the block is the continuation
                # of a previous one
                elif _is_continued_block(line):
                    last_group.extend(line)
                else:
                    new_group = group_cls(last_group, last_created_group)
                    last_created_group = new_group
                    yield new_group
                    last_group = line.copy()

            # otherwise put it in the current group
            else:
                last_group.extend(line)
        # if the last group is not closed, put it with the others
        if last_group:
            new_group = group_cls(last_group, last_created_group)
            last_created_group = new_group
            yield new_group

    @classmethod
    def iterate_groups_from_source(group_cls, readline):
        lines = group_cls._iterate_input_logical_lines(readline)
        groups = group_cls._iterate_groups(lines)
        for group in groups:
            yield group


# %%
def run_file(input_file, output_dir):
    with open(input_file) as file:
        origins = file.readline
        groups = CodeGroup.iterate_groups_from_source(origins)
        groups = list(groups)
        glob = {}

        pylab_show_cage = MyPylabShow()
        for group in groups:
            group.execute(glob, pylab_show_cage)
            # print(str(group))
            # print('-------------------------')
            # print(group.results)
            # print('=========================')
        # close all the obtained figures, as the pylab act as a singleton
        # and stores them. i you launch any code that use pylab after the
        # execution, it will have all the generated figures.
        import pylab
        pylab.close('all')
        imported_modules = set()
        for key, value in glob.items():
            if type(value) == type(pylab):
                imported_modules.add(value)
        for module in imported_modules:
            pass  # print(module.__name__)
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    filename_complete_rst = output_dir+'compiled.rst'
    compiled_rst = "\n".join(str(group.compile(output_dir))
                             for group in groups)
    with open(filename_complete_rst, 'wt') as rst_file:
        print(compiled_rst, file=rst_file)

    filename_complete_html = output_dir+'compiled.html'
    H = publish_parts(compiled_rst, writer_name='html')['whole']
    with open(filename_complete_html, 'wt') as html_file:
        print(H, file=html_file)
    print("COMPLETED")

# %%

import unittest
source_test_1 = '''
#not docstring
a = 5

#comment 2
"""docstring"""

"""docstring"""

"not docstring"; a = 5
'''

source_test_if_else = '''
if False:
    pass
elif 0:
    pass
else:
    pass
'''

source_test_for_else = '''
for i in range(1):
    pass
else:
    pass
'''

source_test_try_except = '''
try:
    pass
except:
    pass
else:
    pass
finally:
    pass
'''


class test_Group(unittest.TestCase):

    def generate_groups(self, source_code):
        """generates the groups from the given source code
        boilerplate code"""
        origin = StringIO(source_code).readline
        groups = CodeGroup.iterate_groups_from_source(origin)
        return groups

    def test_is_docstring_1(self):
        """On the given source code, check which are proper strings that
        will be Weaved out.
        """
        groups = self.generate_groups(source_test_1)
        expected = [False, True, True, False]
        observed = [bool(g.is_docstring()) for g in groups]
        self.assertEqual(expected, observed)

    def test_recomposition_trailing_white_line(self):
        """if the source file has no trailing white line the reconstructed
        source code correspond to the original.
        No garantee if it is not following the proper format

        If it is missing the last newline, it is going to miss the last
        group!
        """
        # FIXME: it need to manage correctly the last newline
        groups = self.generate_groups(source_test_1)
        generated = "".join(str(g) for g in groups)
        self.assertEqual(generated, source_test_1)

    def test_simple_output(self):
        code = "print(1)\n"
        groups = self.generate_groups(code)
        group0 = list(groups)[0]
        res = group0.execute({}, MyPylabShow())
        self.assertEqual(res['standard output'], '1\n')
        self.assertEqual(res['standard error'], '')
        self.assertEqual(res['generated figures'], [])
        self.assertEqual(res['exceptions generated'], None)

    def no_test_simple_exception_output(self):
        code = "raise ValueError('error')\n"
        groups = self.generate_groups(code)
        group0 = list(groups)[0]
        res = group0.execute({}, MyPylabShow())
        self.assertEqual(res['standard output'], '')
        # TODO: check for what is shown in the standard error
        # when an exception is raised
        # err = res['standard error']
        # self.assertEqual(err, '')
        self.assertEqual(res['generated figures'], [])
        e = res['exceptions generated']
        self.assertEqual(e.args, ('error', ))
        self.assertIsInstance(e, ValueError)

    def test_main_section(self):
        code = "if __name__ == '__main__':\n\tprint(5)\n"
        groups = self.generate_groups(code)
        group0 = list(groups)[0]
        res = group0.execute({}, MyPylabShow())
        self.assertEqual(res['standard output'], '5\n')

    def test_grouping_if_else(self):
        groups = self.generate_groups(source_test_if_else)
        groups = list(groups)
        self.assertEqual(len(groups), 1)

    def test_grouping_for_else(self):
        groups = self.generate_groups(source_test_for_else)
        groups = list(groups)
        self.assertEqual(len(groups), 1)

    def test_grouping_try_except(self):
        groups = self.generate_groups(source_test_try_except)
        groups = list(groups)
        self.assertEqual(len(groups), 1)


if __name__ == '__main__':
    b_dir = '/home/PERSONALE/enrico.giampieri2/progetti/literate.py/'
    i_file = b_dir + 'introduction.py'
    o_dir = b_dir + 'compile/'
    run_file(i_file, o_dir)
    unittest.main()


# %%
'''
from IPython.display import HTML, display
from docutils.core import publish_parts

#token_0 = tokenize.TokenInfo(type=tokenize.COMMENT,
string='# %%', start=(0, 0), end=(0, 0), line='\n')

# remove all the comments, but keep all the block header comment
tokens_proper = [tok for tok in tokens if (tok.type!=tokenize.COMMENT or
                                            tok.string.startswith('# %%'))]


# %%
valid_docstrings = []
plausible_docstring = True
plausible_seq = []
for idx, tok in enumerate(tokens_proper):
    if tok.type in [tokenize.INDENT, tokenize.COMMENT, tokenize.DEDENT]:
        "the only possible comment left are the block start"
        plausible_docstring = True
    elif plausible_docstring and tok.type in [tokenize.NL]:
        "after a good condition you should ignore the newline"
        pass
    elif plausible_docstring and tok.type==tokenize.STRING:
        plausible_seq.append(tok)
    elif plausible_docstring and tok.type in [tokenize.NEWLINE]:
        valid_docstrings.extend(plausible_seq)
        plausible_seq = []
        plausible_docstring = False
    else:
        plausible_seq = []
        plausible_docstring = False
    print(tok)
    print(plausible_docstring)
    print(plausible_seq)
    print()


# http://stackoverflow.com/questions/1769332/script-to-remove-python-comments-docstrings
#( DEDENT+ | INDENT? ) STRING+ COMMENT? NEWLINE
# %%

for docstring in valid_docstrings:
    print(docstring.string)
    print()

text = valid_docstrings[0].string
# %%

from pygments import highlight
from pygments.formatters import HtmlFormatter
from pygments.lexers import get_lexer_by_name
from IPython.display import HTML, display, display_html


lexer = get_lexer_by_name("python", stripall=True)
formatter = HtmlFormatter(linenos=True, cssclass="source", style='colorful')

H = highlight(text, lexer, formatter)
print(H)
HTML(H)
# %%



# %%
H = publish_parts(text, writer_name='html')['html_body']
print(H)
HTML(H)
# %%

from contextlib import contextmanager
from datetime import datetime
now = datetime.now

@contextmanager
def Timer():
    start = now()
    yield
    end = now()-start
    print(end)

# %%

from modulefinder import ModuleFinder
finder = ModuleFinder()
finder.run_script(data_dir+filename)

# %%
print( 'Loaded modules:')
for name, mod in finder.modules.items():
    print( '%s: ' % name,)
    #keys = mod.globalnames.keys()
    #print( ','.join(list(keys)[:3]))

#print( '-'*50)
#print( 'Modules not imported:')
#print( '\n'.join(finder.badmodules.keys()))
# %%

from modulefinder import ModuleFinder
f = ModuleFinder()

# Run the main script
f.run_script(filename)

# Get names of all the imported modules
names = list(f.modules.keys())

# Get a sorted list of the root modules imported
basemods = sorted(set([name.split('.')[0] for name in names]))
# Print it nicely
#print("\n".join(basemods) )
# %%
for module in basemods[:]:
    try:
        module = __import__(module)
        version = module.__version__
        name = module.__name__
        print(name, version)
    except ImportError:
        pass
    except AttributeError:
        pass
'''