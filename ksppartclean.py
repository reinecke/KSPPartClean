#! /usr/bin/env python
"""
MIT License

Copyright (c) 2017 Eric Reinecke

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""
import os
import sys
import itertools


class KSPNode:
    """
    Class encapsulating a node in a KSP save file.

    This class support using subscription to get and assign values to the
    parameters. However since a node may have many parameters with the same
    key, only the first one will be gotten or set.
    """

    key = None
    """ The Node key (sort of the type)."""
    parameters = None
    """
    A list of tuples of keys and values.

    Commonly there are duplicate entries for a given key.
    """
    children = None
    """
    A list of child KSPNodes.
    """

    def __init__(self, key):
        self.key = key
        self.parameters = []
        self.children = []

    def __repr__(self):
        return '<{}({})>'.format(
                'KSPNode',
                repr(self.key)
        )

    def children_with_key(self, child_key):
        """
        Returns a list of this node's children with the provided key.
        """
        return [
                c for c in self.children
                if c.key == child_key
        ]

    def __getitem__(self, key):
        try:
            return [v for k, v in self.parameters if k == key][0]
        except IndexError:
            raise KeyError(key)

    def __setitem__(self, key, value):
        found_idx = None
        for i, pair in enumerate(self.parameters):
            if pair[0] == key:
                found_idx = i
                break

        if found_idx is None:
            self.parameters.append((key, value))
        else:
            self.parameters[found_idx] = (key, value)

    def node_text(self, prefix=''):
        '''
        returns the text serialization text of the node.
        '''
        txt = '{pfx}{key}\n{pfx}{{'.format(
                pfx=prefix,
                key=self.key
        )

        for param in self.parameters:
            k, v = param
            txt += '\n{pfx}\t{k} = {v}'.format(
                    pfx=prefix,
                    k=k,
                    v=v
            )

        for child in self.children:
            child_text = child.node_text('\t'+prefix)
            txt += '\n{}'.format(child_text)

        txt += '\n{pfx}}}'.format(pfx=prefix)
        return txt


def read_one_node(f, key):
    """
    Reads the node (and it's childeren) from the provided open file object.

    The file pointer is expected to be on the line where the ``{`` start of
    the node is. It is expected the key was already parsed from the file
    and passed in.
    """
    n = KSPNode(key)

    for line in f:
        cleanline = line.strip()
        if cleanline == '{':
            continue
        elif cleanline == '}':
            # end of node
            return n
        elif '=' in cleanline:
            pair = line.strip('\n').split('=')
            k = pair[0].strip()
            if len(pair) == 1:
                v = ''
            else:
                v = pair[1][1:]
            n.parameters.append((k, v))
        else:
            # New node name, recurse
            child_node = read_one_node(f, cleanline)
            n.children.append(child_node)


def load_file(fpath):
    """
    Loads the KSP save file with the provided path and returns a list of
    top-level KSPNode instances.
    """
    root_nodes = []

    with open(fpath) as f:
        for line in f:
            clean_line = line.strip()
            n = read_one_node(f, clean_line)
            root_nodes.append(n)

    return root_nodes


def scrub_parts_by_name(vessel, part_names):
    """
    Removes parts from the provided vessel that have names in the part_names
    list.
    """
    new_parts_list = []
    deleted_part_indexes = set()
    part_id = 0
    for child_id, child in enumerate(vessel.children):
        if child.key != 'PART':
            new_parts_list.append(child)
            continue
        elif child['name'] in part_names:
            deleted_part_indexes.add(part_id)
        else:
            new_parts_list.append(child)
        part_id += 1

    # Now, re-parent the parts
    for part in new_parts_list:
        if part.key != 'PART':
            continue

        # Find the count to offset the parent id by
        new_parameters = []
        for k, v in part.parameters:
            if k in ['sym', 'parent']:
                ref_id = int(v)
            elif k in ['srfN', 'attN']:
                attach_type, ref_id = v.split(', ')
                ref_id = int(ref_id)
            else:
                # no-op and pass-through parameter
                new_parameters.append((k, v))
                continue

            if ref_id in deleted_part_indexes:
                raise Exception(
                        'Cannot re-parent if parent was deleted: {} {}'.format(
                            part['name'],
                            k
                        )
                )

            id_offset = len([i for i in deleted_part_indexes if i < ref_id])

            if ref_id != -1:
                new_ref_id = ref_id - id_offset
            else:
                new_ref_id = ref_id

            if k in ['srfN', 'attN']:
                # Re-join the value list
                new_v = ', '.join([attach_type, str(new_ref_id)])
            else:
                new_v = str(new_ref_id)

            new_parameters.append((k, new_v))

        part.parameters = new_parameters

    vessel.children = new_parts_list


def all_parts_used(root_node):
    """
    Returns a set of all the names for parts used in the given save file root
    node.
    """
    fs = root_node.children_with_key('FLIGHTSTATE')[0]
    vessels = fs.children_with_key('VESSEL')
    all_parts = itertools.chain(
            *(
                (p['name']for p in vessel.children if p.key == 'PART')
                for vessel in vessels
            )
    )

    return set(all_parts)


def purge_parts(root_node, part_names):
    """
    Purges parts in the given list of part_names under the provided save file
    root node.
    """
    fs = root_node.children_with_key('FLIGHTSTATE')[0]
    vessels = fs.children_with_key('VESSEL')
    for vessel in vessels:
        orig_part_count = len(vessel.children)
        scrub_parts_by_name(vessel, part_names)
        deleted_part_count = orig_part_count - len(vessel.children)
        if deleted_part_count > 0:
            print(
                'Deleted {} parts from {}'.format(
                    deleted_part_count,
                    vessel['name']
                )
            )


def main():
    # TODO: use Argparse instead
    fpath = sys.argv[1]
    if not os.path.isfile(fpath):
        print('No such file: {}'.format(fpath))
        return 1

    try:
        root_node = load_file(fpath)[0]
        if len(sys.argv) == 2:
            # Just print a parts lists
            print(
                '\n'.join(
                    sorted(all_parts_used(root_node), key=lambda s: s.lower())
                )
            )
            return 0

        # Decide what to call the output file
        parent_dir, fname = os.path.split(fpath)
        name, ext = os.path.splitext(fname)
        outfile = os.path.join(parent_dir, '{}.cleaned{}'.format(name, ext))
        if os.path.exists(outfile):
            print(
                'Please move existing output file before running: {}'.format(
                    outfile
                )
            )
            return 1

        # Purge all the provided parts
        part_names = sys.argv[2:]
        print('purging parts with names: {}'.format(', '.join(part_names)))

        # Remove the parts
        purge_parts(root_node, part_names)

        with open(outfile, 'w') as f:
            f.write(root_node.node_text())

        print('Wrote scrubbed file to: {}'.format(outfile))
    except Exception as e:
        print(
            'An error was encountered and file editing was aborted: {}'.format(
                e
            )
        )
        return 2

    return 0


if __name__ == '__main__':
    sys.exit(main())
