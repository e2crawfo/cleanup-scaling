from hrr_scaling.neural_extraction import NeuralExtraction

import random
import string

import matplotlib.pyplot as plt
import numpy as np
import matplotlib.gridspec as gridspec

import nengo
from nengo.dists import Uniform
from nengo.utils.ensemble import tuning_curves


def plot_performance(y_vals, error_lo, error_hi, measure_labels,
                     condition_labels, filename='', show=False, colors=None,
                     **kwargs):
    """
    Plot bar chart with error bars. A measure is some specific dimension that
    we want to compare different conditions on. A condition is some
    configuration of parameters that we want to compare on different measures.

    E.g. two conditions could be 'model' and 'experiment', and the measures
    would be aspects of the performance that we want to compare them on.

    In the bar chart, each condition is assigned a color. Each measure gets a
    locations on the graph, where bars from each condition will be displayed.
    """

    import matplotlib as mpl
    if show:
        mpl.use('Qt4Agg')
    else:
        mpl.use('Agg')
    import matplotlib.pyplot as plt

    assert(len(y_vals[0]) ==
           len(error_lo[0]) ==
           len(error_hi[0]))

    assert(len(y_vals) ==
           len(error_lo) == len(error_hi))

    # this is the number of different bar locations
    # typically each location is a measure
    try:
        num_measures = len(y_vals[0])
    except IndexError:
        raise ValueError("y_vals must be a 2D array/list")

    # this is the number of bars at each location...typically a set of
    # conditions that we want to compare on multiple measures
    try:
        num_conditions = len(y_vals)
    except Exception:
        raise ValueError("y_vals must be a 2D array/list")

    if not measure_labels:
        measure_labels = [''] * num_measures

    if not condition_labels:
        condition_labels = [''] * num_conditions

    assert(len(measure_labels) == num_measures)
    assert(len(condition_labels) == num_conditions)

    print num_measures, num_conditions

    # hatch = ['/', '|||||', '\\', 'xxx', '||', '--', '+', 'OO', '...', '**']
    if not colors:
        colors = [np.ones(3) * l for l in np.linspace(.1, .9, num_conditions)]

    cross_measurement_spacing = 0.4
    within_measurement_spacing = 0.0
    bar_width = 0.4

    error_lo = [[y - el for y, el in zip(yvl, ell)]
                for yvl, ell in zip(y_vals, error_lo)]
    error_hi = [[eh - y for y, eh in zip(yvl, ehl)]
                for yvl, ehl in zip(y_vals, error_hi)]

    # mpl.rc('font', family='serif', serif='Times New Roman')
    # mpl.rcParams['lines.linewidth'] = 0.3

    fig = plt.figure(figsize=(5, 2.55))

    mpl.rcParams.update({'font.size': 7})

    # plt.title("Model Performance")
    plt.ylabel("\% Correct")

    bar_left_positions = [[] for b in range(num_conditions)]
    val_offset = 0
    middles = []
    for i in range(num_measures):
        val_offset += cross_measurement_spacing

        left_side = val_offset

        for j in range(num_conditions):
            if j > 0:
                val_offset += within_measurement_spacing
                val_offset += bar_width

            bar_left_positions[j].append(val_offset)

        val_offset += bar_width

        right_side = val_offset

        middles.append(float(left_side + right_side) / 2.0)

    zipped = zip(
        bar_left_positions, y_vals, colors,
        error_lo, error_hi, condition_labels)

    for blp, yv, cl, el, eh, lb in zipped:
        plt.bar(
            blp, yv, color=cl, width=bar_width, linewidth=0.2,
            yerr=[el, eh], ecolor="black", label=lb,
            error_kw={"linewidth": 0.5, "capsize": 2.0})

    plt.legend(
        loc='center left', bbox_to_anchor=(1, 0.5), prop={'size': 7},
        handlelength=.75, handletextpad=.5, shadow=False, frameon=False)

    ax = fig.axes[0]
    box = ax.get_position()
    ax.set_position([box.x0, box.y0, box.width * 0.8, box.height])
    handles, labels = ax.get_legend_handles_labels()

    ticks = middles

    plt.xticks(ticks, measure_labels)
    plt.ylim([0.0, 105.0])
    plt.xlim([0.0, val_offset + cross_measurement_spacing])
    plt.axhline(100.0, linestyle='--', color='black')

    plt.subplots_adjust(left=0.2, right=0.8, top=0.9, bottom=0.1)

    if filename:
        plt.savefig(filename)

    if show:
        plt.show()


def plot_tuning_curves(filename, plot_decoding=False, show=False):
    """
    Plot tuning curves for an association population and for a standard
    subpopulation (of the neural extraction network).
    """
    import matplotlib as mpl
    mpl.rcParams['font.size'] = '10'

    if show:
        mpl.use('Qt4Agg')
    else:
        mpl.use('Agg')

    import matplotlib.pyplot as plt

    plt.figure(figsize=(5, 3))

    neurons_per_item = 20
    neurons_per_dim = 50
    intercepts_low = 0.29
    intercepts_range = 0.00108

    intercepts = Uniform(intercepts_low, intercepts_low + intercepts_range)

    tau_rc = 0.034
    tau_ref = 0.0025
    radius = 1.0
    assoc_encoders = np.ones((neurons_per_item, 1))
    standard_encoders = np.ones((neurons_per_dim, 1))

    threshold = 0.3
    threshold_func = lambda x: 1 if x > threshold else 0

    max_rates = Uniform(200, 350)

    model = nengo.Network("Associative Memory")
    with model:
        neuron_type = nengo.LIF(
            tau_rc=tau_rc, tau_ref=tau_ref)

        assoc = nengo.Ensemble(
            n_neurons=neurons_per_item, dimensions=1, intercepts=intercepts,
            encoders=assoc_encoders, label="assoc", radius=radius,
            max_rates=max_rates, neuron_type=neuron_type)

        n_eval_points = 750
        eval_points = np.random.normal(0, 0.06, (n_eval_points, 1))
        eval_points.T[0].sort()
        radius = 5.0 / np.sqrt(512)
        standard = nengo.Ensemble(n_neurons=neurons_per_dim, dimensions=1,
                                  eval_points=eval_points, radius=radius,
                                  encoders=standard_encoders)

        if plot_decoding:
            dummy = nengo.Ensemble(1, 1)
            conn = nengo.Connection(assoc, dummy, function=threshold_func)
            dummy2 = nengo.Ensemble(1, 1)
            conn2 = nengo.Connection(standard, dummy2)

    sim = nengo.Simulator(model)

    if plot_decoding:
        gs = gridspec.GridSpec(3, 2)
    else:
        gs = gridspec.GridSpec(2, 2)

    plt.subplot(gs[0:2, 0])

    assoc_eval_points, assoc_activities = tuning_curves(assoc, sim)

    for neuron in assoc_activities.T:
        plt.plot(assoc_eval_points.T[0], neuron)
    plt.title("Association")
    plt.ylabel("Firing Rate (spikes/s)")
    plt.xlabel(r"$e_ix$")
    plt.ylim((0, 400))
    plt.yticks([0, 100, 200, 300, 400])

    ax = plt.subplot(gs[0:2, 1])

    # We want different eval points for display purposes than for
    # optimization purposes
    eval_points = Uniform(-radius, radius).sample(n_eval_points)
    eval_points.sort()
    eval_points = eval_points.reshape((n_eval_points, 1))

    # have to divide by radius on our own since tuning_curves skips that step
    _, activities = tuning_curves(standard, sim, eval_points/radius)
    for neuron in activities.T:
        plt.plot(eval_points, neuron)

    plt.title("Standard")
    plt.xlabel(r"$e_ix$")
    plt.xlim((-radius, radius))
    plt.ylim((0, 400))
    plt.setp(ax, yticks=[])

    if plot_decoding:
        plt.subplot(gs[2, 0])
        decoders = sim.data[conn].decoders
        plt.plot(assoc_eval_points.T[0],
                 0.001 * np.dot(assoc_activities, decoders.T))
        plt.axhline(y=1.0, ls='--')

        plt.subplot(gs[2, 1])
        x, activities2 = tuning_curves(standard, sim, assoc_eval_points/radius)
        decoders = sim.data[conn2].decoders
        plt.plot(
            assoc_eval_points.T[0],
            0.001 * np.dot(activities2, decoders.T))
        plt.plot([-1.0, 1.0], [-1.0, 1.0], c='k', ls='--')
        plt.axvline(x=radius, c='k', ls='--')
        plt.axvline(x=-radius, c='k', ls='--')

    plt.tight_layout()

    plt.subplots_adjust(right=0.89, left=0.11)

    if filename:
            plt.savefig(filename)
    if show:
            plt.show()


def chain_simulation_data(dimension=512, num_synsets=-1,
                          num_links=4, num_others=0, starting_word=None):

    input_dir = 'wordnet_data'
    output_dir = 'results'

    unitary_relations = False
    proportion = 1.0

    collect_spikes = True

    vc = VectorizedCorpus(
        dimension, input_dir, unitary_relations,
        proportion, num_synsets, create_namedict=True)

    starting_keys = []
    if starting_word:
        starting_keys = [starting_word]

    chain = vc.find_chain(num_links, starting_keys=starting_keys).next()
    names = [vc.key2name[c] for c in chain]

    if num_others > 0:
        other_keys = vc.semantic_pointers.keys()
        other_keys = filter(lambda o: o not in chain, other_keys)
        num_others = min(num_others, len(other_keys))
        others = random.sample(other_keys, num_others)

    id_vectors = vc.id_vectors
    semantic_pointers = vc.semantic_pointers

    query_vector = vc.relation_type_vectors['@']

    extractor = NeuralExtraction(
        id_vectors, semantic_pointers, threshold=0.3,
        output_dir=output_dir, probe_keys=chain,
        timesteps=100, synapse=0.005,
        plot=False, show=False, ocl=False, gpus=[0],
        identical=True, collect_spikes=collect_spikes)

    input_probe = extractor.input_probe
    D_probe = extractor.D_probe
    output_probe = extractor.output_probe

    sim = extractor.simulator

    extractor.A_input_vector = semantic_pointers[chain[0]]
    extractor.B_input_vector = query_vector

    for i in range(num_links):
        print "Starting link %d" % i

        if i:
            extractor.A_input_vector = sim.data[output_probe][-1, :]

        sim.run(0.1)

    t = sim.trange()

    # -------------
    chain_sp = [semantic_pointers[c][:, np.newaxis] for c in chain]
    chain_sp = np.concatenate(chain_sp, axis=1)

    synset = np.dot(sim.data[input_probe], chain_sp)

    chain_id = [id_vectors[c][:, np.newaxis] for c in chain]
    chain_id = np.concatenate(chain_id, axis=1)

    before = np.dot(sim.data[D_probe], chain_id)
    after = np.dot(sim.data[output_probe], chain_sp)

    # -------------
    if num_others:
        other_id = [id_vectors[o][:, np.newaxis] for o in others]
        other_id = np.concatenate(other_id, axis=1)

        other_before = np.dot(sim.data[D_probe], other_id)
        other_before = np.max(other_before, axis=1)[:, np.newaxis]

        before = np.concatenate((before, other_before), axis=1)

        names.append('Other')

    # -------------
    spikes = np.array([])
    if collect_spikes:
        spike_probes = extractor.assoc_spike_probes
        spikes = [sim.data[spike_probes[key]] for key in chain]
        spikes = np.concatenate(spikes, axis=1)

    return {'names': names, 't': t, 'synset': synset,
            'before': before, 'after': after, 'spikes': spikes}


def chain_simulation_plot(names, t, synset, before,
                          after, spikes, bw=True, filename=None):

    if 'Other' in names:
        raise ValueError("Plotting of 'Other' label not implemented")

    names = [string.replace(n, '_', ' ') for n in names]

    timesteps = len(t)

    synset = synset[:timesteps, :]
    before = before[:timesteps, :]
    after = after[:timesteps, :]
    spikes = spikes[:timesteps, :]

    print "Plotting"

    plt.figure(figsize=(7, 6.5))

    gs = gridspec.GridSpec(4, 1)

    if bw:
        linestyles = ['-'] * len(names)
        colors = map(lambda n: (n, n, n), np.linspace(0, 0.9, len(names)))
    else:
        linestyles = ['-'] * len(names)
        colors = [None] * len(names)

    linewidth = 1.6
    text_offset_x = -0.13
    text_offset_y = 0.95

    ylim = (-0.4, 1.3)
    yticks = [0, 0.5, 1.0]

    def do_plot(index, sims, y_label):
        ax = plt.subplot(gs[index, 0])

        lines = []

        for s, ls, n, c in zip(sims.T, linestyles, names, colors):
            line = plt.plot(t, s, ls=ls, lw=linewidth, c=c)
            lines.extend(line)

        plt.ylabel(y_label)
        plt.ylim(ylim)

        return ax, lines

    # --------------------
    y_label = 'Dot Product'
    ax, lines = do_plot(0, synset, y_label)
    plt.setp(ax, xticks=[])
    plt.yticks(yticks)
    ax.text(
        text_offset_x, text_offset_y, r'\textbf{a)}',
        transform=ax.transAxes)

    plt.legend(lines, names, loc=4, fontsize='xx-small')

    # --------------------
    y_label = 'Dot Product'
    ax, lines = do_plot(1, before, y_label)
    plt.setp(ax, xticks=[])
    plt.yticks(yticks)
    ax.text(
        text_offset_x, text_offset_y, r'\textbf{b)}',
        transform=ax.transAxes)

    # --------------------
    ax = plt.subplot(gs[2, 0])

    if spikes.size > 0:
        n_assoc_neurons = int(spikes.shape[1] / len(names))

        if bw:
            nengo.utils.matplotlib.rasterplot(t, spikes, ax, colors=['k'])
        else:
            colors = [plt.getp(line, 'color') for line in lines]
            spike_colors = [colors[int(i / n_assoc_neurons)]
                            for i in range(spikes.shape[1])]

            nengo.utils.matplotlib.rasterplot(
                t, spikes, ax, colors=spike_colors)

        plt.setp(ax, xticks=[])

        short_names = [string.replace(s, ' ', '\n') for s in names]
        spike_ticks = n_assoc_neurons * np.arange(len(names))
        spike_ticks += n_assoc_neurons / 2.0

        plt.yticks(
            spike_ticks, short_names, fontsize='xx-small')

        light_gray = [0.95] * 3

        for i in range(len(names)):
            if i % 2 == 1:
                plt.axhspan(i * n_assoc_neurons,
                            (i + 1) * n_assoc_neurons,
                            color=light_gray)

        ax.text(
            text_offset_x, text_offset_y, r'\textbf{c)}',
            transform=ax.transAxes)

    # --------------------
    y_label = 'Dot Product'
    ax, lines = do_plot(3, after, y_label)
    plt.xlabel('Time (s)')
    plt.yticks(yticks)
    ax.text(
        text_offset_x, text_offset_y, r'\textbf{d)}',
        transform=ax.transAxes)

    plt.subplots_adjust(
        top=0.97, right=0.89, bottom=0.07, left=0.11, hspace=0.08)

    if filename:
        plt.savefig(filename)
    else:
        plt.show()


def chain_simulation(filename, dimension=128, num_synsets=50, num_links=3):
    data = chain_simulation_data(dimension, num_synsets, num_links)
    chain_simulation_plot(filename=filename, **data)


if __name__ == "__main__":

    data = chain_simulation_data()
    chain_simulation_plot(*data, filename="chain_sim.pdf")
