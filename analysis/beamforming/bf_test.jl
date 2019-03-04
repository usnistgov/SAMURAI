#beamforming testing in julia

#3d positions structure
struct points_3d_t{T}
    x::Array{T}
    y::Array{T}
    z::Array{T}
end

#locations type. array of x,y,z values
locations_t = points_3d_t{Float64}

#spherical coordinate structure
struct spherical_coord_t{T}
    rho::T
    phi::T
    theta::T
end

#angle type
angles_t = spherical_coord{Array{Float64}}


function get_beamformed_value(locations::locations_t,angle::angles_t,freq_hz,s21_vals::Array{Complex})
    #===
     @brief get a beamformed value at a given angle from array elements at location with given s21 values
     @param[in] locations - structure containing x,y,z locations (in meters) of array elements
     @param[in] angle - structure containing a array of spherical coordinates (rho doesnt matter) of the angle to look at
     @param[in] freq_hz - frequency of the data in hz
     @param[in] s21_vals - array of complex values corresponding to recieved values at locations x,y,z
     @return beam steered value at the given angle
    ===#
    for i=1:length(a) #loop through each beamformed elements


end