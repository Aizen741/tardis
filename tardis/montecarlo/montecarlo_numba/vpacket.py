from numba import float64, int64, jitclass
import numpy as np

from tardis.montecarlo.montecarlo_numba.rpacket import (
    calculate_distance_boundary, get_doppler_factor, calculate_distance_line,
    calculate_tau_electron, PacketStatus, move_packet_across_shell_boundary)

vpacket_spec = [
    ('r', float64),
    ('mu', float64),
    ('nu', float64),
    ('energy', float64),
    ('next_line_id', int64),
    ('current_shell_id', int64),
    ('status', int64)
]

@jitclass(vpacket_spec)
class VPacket(object):
    def __init__(self, r, mu, nu, energy):
        self.r = r
        self.mu = mu
        self.nu = nu
        self.energy = energy
        self.current_shell_id = -1
        self.next_line_id = -1
        self.status = -1

    def move_vpacket(self, distance):
        """Move packet a distance and recalculate the new angle mu

        Parameters
        ----------
        distance : float
            distance in cm
        """
        r = self.r
        if (distance > 0.0):
            new_r = np.sqrt(r ** 2 + distance ** 2 +
                            2.0 * r * distance * self.mu)
            self.mu = (self.mu * r + distance) / new_r
            self.r = new_r

    def move_packet_across_shell_boundary(self, distance, delta_shell,
                                          no_of_shells):
        """
        Move packet across shell boundary - realizing if we are still in the simulation or have
        moved out through the inner boundary or outer boundary and updating packet
        status.

        Parameters
        ----------
        distance : float
            distance to move to shell boundary

        delta_shell: int
            is +1 if moving outward or -1 if moving inward

        no_of_shells: int
            number of shells in TARDIS simulation
        """

        next_shell_id = r_packet.current_shell_id + delta_shell

        if next_shell_id >= no_of_shells:
            r_packet.status = PacketStatus.EMITTED
        elif next_shell_id < 0:
            r_packet.status = PacketStatus.REABSORBED
        else:
            rpacket.current_shell_id = next_shell_id


@njit(**njit_dict)
def trace_vpacket_within_shell(v_packet, numba_model, numba_plasma):
    
    r_inner = numba_model.r_inner[v_packet.current_shell_id]
    r_outer = numba_model.r_outer[v_packet.current_shell_id]

    distance_boundary, delta_shell = calculate_distance_boundary(
        v_packet.r, v_packet.mu, r_inner, r_outer)

    # defining start for line interaction
    start_line_id = v_packet.next_line_id

    # defining taus
    

    # e scattering initialization
    cur_electron_density = numba_plasma.electron_density[
        v_packet.current_shell_id]
    tau_electron = calculate_tau_electron(cur_electron_density, 
                                            distance_boundary)
    tau_trace_combined = tau_electron

    # Calculating doppler factor
    doppler_factor = get_doppler_factor(v_packet.r, v_packet.mu,
                                        numba_model.time_explosion)
    comov_nu = v_packet.nu * doppler_factor
    cur_line_id = start_line_id

    for cur_line_id in range(start_line_id, len(numba_plasma.line_list_nu)):
        nu_line = numba_plasma.line_list_nu[cur_line_id]
        tau_trace_line = numba_plasma.tau_sobolev[
            cur_line_id, v_packet.current_shell_id]

        tau_trace_combined += tau_trace_line
        distance_trace_line = calculate_distance_line(
            v_packet.nu, comov_nu, nu_line, numba_model.time_explosion)

        if (distance_boundary <= distance_trace_line):
            v_packet.next_line_id = cur_line_id
            break

    v_packet.next_line_id = cur_line_id
    return tau_trace_combined, distance_boundary, delta_shell


def trace_vpacket(v_packet, numba_model, numba_plasma):
    tau_trace_combined = 0.0
    while True:
        tau_trace_combined_shell, distance_boundary, delta_shell = trace_vpacket_within_shell(
            v_packet, numba_model, numba_plasma
        )
        tau_trace_combined += tau_trace_combined_shell
        move_packet_across_shell_boundary(v_packet, delta_shell,
                                            no_of_shells)
        if v_packet.status == PacketStatus.EMITTED:
            break

        # Moving the v_packet
        new_r = np.sqrt(v_packet.r**2 + distance_boundary**2 +
                         2.0 * v_packet.r * distance_boundary * v_packet.mu)
        v_packet.mu = (v_packet.mu * v_packet.r + distance_boundary) / new_r
        v_packet.r = new_r

    double
    mu_bin = (1.0 - mu_min) / rpacket_get_virtual_packet_flag(packet);
    rpacket_set_mu( & virt_packet, mu_min + (i + rk_double(mt_state)) * mu_bin);
    {
      if ((rpacket_get_nu (packet) > storage->spectrum_virt_start_nu) && (rpacket_get_nu(packet) < storage->spectrum_virt_end_nu))
        {
          for (int64_t i = 0; i < rpacket_get_virtual_packet_flag (packet); i++)
            {
              double weight;
              rpacket_t virt_packet = *packet;
              double mu_min;
              if (rpacket_get_r(&virt_packet) > storage->r_inner[0])
                {
                  mu_min =
                    -1.0 * sqrt (1.0 -
                                 (storage->r_inner[0] / rpacket_get_r(&virt_packet)) *
                                 (storage->r_inner[0] / rpacket_get_r(&virt_packet)));

                  if (storage->full_relativity)
                    {
                      // Need to transform the angular size of the photosphere into the CMF
                      mu_min = angle_aberration_LF_to_CMF (&virt_packet, storage, mu_min);
                    }
                }
              else
                {
                  mu_min = 0.0;
                }
              double mu_bin = (1.0 - mu_min) / rpacket_get_virtual_packet_flag (packet);
              rpacket_set_mu(&virt_packet,mu_min + (i + rk_double (mt_state)) * mu_bin);
              switch (virtual_mode)
                {
                case -2:
                  weight = 1.0 / rpacket_get_virtual_packet_flag (packet);
                  break;
                case -1:
                  weight =
                    2.0 * rpacket_get_mu(&virt_packet) /
                    rpacket_get_virtual_packet_flag (packet);
                  break;
                case 1:
                  weight =
                    (1.0 -
                     mu_min) / 2.0 / rpacket_get_virtual_packet_flag (packet);
                  break;
                default:
                  fprintf (stderr, "Something has gone horribly wrong!\n");
                  // FIXME MR: we need to somehow signal an error here
                  // I'm adding an exit() here to inform the compiler about the impossible path
                  exit(1);
                }
              angle_aberration_CMF_to_LF (&virt_packet, storage);
              double doppler_factor_ratio =
                rpacket_doppler_factor (packet, storage) /
                rpacket_doppler_factor (&virt_packet, storage);
              rpacket_set_energy(&virt_packet,
                                 rpacket_get_energy (packet) * doppler_factor_ratio);
              rpacket_set_nu(&virt_packet,rpacket_get_nu (packet) * doppler_factor_ratio);
              reabsorbed = montecarlo_one_packet_loop (storage, &virt_packet, 1, mt_state);
#ifdef WITH_VPACKET_LOGGING
#ifdef WITHOPENMP
#pragma omp critical
                {
#endif // WITHOPENMP
                  if (storage->virt_packet_count >= storage->virt_array_size)
                    {
                      storage->virt_array_size *= 2;
                      storage->virt_packet_nus = safe_realloc(storage->virt_packet_nus, sizeof(double) * storage->virt_array_size);
                      storage->virt_packet_energies = safe_realloc(storage->virt_packet_energies, sizeof(double) * storage->virt_array_size);
                      storage->virt_packet_last_interaction_in_nu = safe_realloc(storage->virt_packet_last_interaction_in_nu, sizeof(double) * storage->virt_array_size);
                      storage->virt_packet_last_interaction_type = safe_realloc(storage->virt_packet_last_interaction_type, sizeof(int64_t) * storage->virt_array_size);
                      storage->virt_packet_last_line_interaction_in_id = safe_realloc(storage->virt_packet_last_line_interaction_in_id, sizeof(int64_t) * storage->virt_array_size);
                      storage->virt_packet_last_line_interaction_out_id = safe_realloc(storage->virt_packet_last_line_interaction_out_id, sizeof(int64_t) * storage->virt_array_size);
                    }
                  storage->virt_packet_nus[storage->virt_packet_count] = rpacket_get_nu(&virt_packet);
                  storage->virt_packet_energies[storage->virt_packet_count] = rpacket_get_energy(&virt_packet) * weight;
                  storage->virt_packet_last_interaction_in_nu[storage->virt_packet_count] = storage->last_interaction_in_nu[rpacket_get_id (packet)];
                  storage->virt_packet_last_interaction_type[storage->virt_packet_count] = storage->last_interaction_type[rpacket_get_id (packet)];
                  storage->virt_packet_last_line_interaction_in_id[storage->virt_packet_count] = storage->last_line_interaction_in_id[rpacket_get_id (packet)];
                  storage->virt_packet_last_line_interaction_out_id[storage->virt_packet_count] = storage->last_line_interaction_out_id[rpacket_get_id (packet)];
                  storage->virt_packet_count += 1;
#ifdef WITHOPENMP
                }
#endif // WITHOPENMP
#endif // WITH_VPACKET_LOGGING
              if ((rpacket_get_nu(&virt_packet) < storage->spectrum_end_nu) &&
                  (rpacket_get_nu(&virt_packet) > storage->spectrum_start_nu))
                {
#ifdef WITHOPENMP
#pragma omp critical
                    {
#endif // WITHOPENMP
                      int64_t virt_id_nu =
                        floor ((rpacket_get_nu(&virt_packet) -
                                storage->spectrum_start_nu) /
                               storage->spectrum_delta_nu);
                      storage->spectrum_virt_nu[virt_id_nu] +=
                        rpacket_get_energy(&virt_packet) * weight;
#ifdef WITHOPENMP
                    }
#endif // WITHOPENMP
                }
            }
        }
      else
        {
          return 1;
        }