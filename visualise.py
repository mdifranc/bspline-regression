# visualise.py

# Imports
import argparse
import json
import numpy as np
import os
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D

from uniform_bspline import Contour


# generate_figure
def generate_figure(z, num_samples, verbose=True):
    degree, num_control_points, dim, is_closed = (
        z['degree'], z['num_control_points'], z['dim'], z['is_closed'])

    if verbose:
        print '  degree:', degree
        print '  num_control_points:', num_control_points
        print '  dim:', dim
        print '  is_closed:', is_closed
    c = Contour(degree, num_control_points, dim, is_closed=is_closed)

    Y, w, u, X = map(lambda k: np.array(z[k]), 'YwuX')
    if verbose:
        print '  num_data_points:', Y.shape[0]

    kw = {}
    if Y.shape[1] == 3:
        kw['projection'] = '3d'
    f = plt.figure()
    ax = f.add_subplot(111, **kw)
    ax.set_aspect('equal')
    def plot(X, *args, **kwargs):
        ax.plot(*(tuple(X.T) + args), **kwargs)

    plot(Y, 'ro')

    for m, y in zip(c.M(u, X), Y):
        plot(np.r_['0,2', m, y], 'k-')

    plot(X, 'bo--', ms=8.0)
    plot(c.M(c.uniform_parameterisation(num_samples), X), 'b-', lw=2.0)

    e = z.get('e')
    if e is not None:
        ax.set_title('Energy: {:.7e}'.format(e))

    return f


# main
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('input_path')
    parser.add_argument('output_path', nargs='?')
    parser.add_argument('--num-samples', type=int, default=1024)
    parser.add_argument('--width', type=float, default=6.0)
    parser.add_argument('--height', type=float, default=4.0)
    parser.add_argument('--dpi', type=int, default=100)
    args = parser.parse_args()

    if os.path.isfile(args.input_path):
        print 'Input:', args.input_path
        with open(args.input_path, 'rb') as fp:
            z = json.load(fp)
        f = generate_figure(z, args.num_samples)
        if args.output_path is None:
            plt.show()
        else:
            print 'Output:', args.output_path
            f.set_size_inches((args.width, args.height))
            f.savefig(args.output_path, dpi=args.dpi,
                      bbox_inches=0.0, pad_inches='tight')
    else:
        if args.output_path is None:
            raise ValueError('`output_path` required')
        if not os.path.exists(args.output_path):
            os.makedirs(args.output_path)

        input_files = sorted(os.listdir(args.input_path),
                             key=lambda f: int(os.path.splitext(f)[0]))
        input_paths = map(lambda f: os.path.join(args.input_path, f),
                          input_files)
        print 'Input:'
        states = []
        for input_path in input_paths:
            print '  ', input_path
            with open(input_path, 'rb') as fp:
                states.append(json.load(fp))

        bounds = sum(map(lambda k: map(lambda z: (np.min(z[k], axis=0),
                                                  np.max(z[k], axis=0)),
                                       states),
                         'XY'),
                     [])
        min_, max_ = zip(*bounds)
        min_, max_ = np.min(min_, axis=0), np.max(max_, axis=0)
        d = 0.01 * (max_ - min_)
        xlim, ylim = np.c_[min_ - d, max_ + d]

        print 'Output:'
        for input_file, z in zip(input_files, states):
            f = generate_figure(z, args.num_samples, verbose=False)

            (ax,) = f.axes
            ax.set_xlim(*xlim)
            ax.set_ylim(*ylim)

            input_stem, _ = os.path.splitext(input_file)
            output_path = os.path.join(args.output_path,
                                       '{}.png'.format(input_stem))
            print '  ', output_path

            f.set_size_inches((args.width, args.height))
            f.savefig(output_path, dpi=args.dpi,
                      bbox_inches=0.0, pad_inches='tight')
            plt.close(f)

if __name__ == '__main__':
    main()
