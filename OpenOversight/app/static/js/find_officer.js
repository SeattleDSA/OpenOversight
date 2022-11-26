function buildSelect(name, data_url, dept_id) {
    return $.get({
        url: data_url,
        data: {department_id: dept_id}
    }).done(function(data) {
        const dropdown = $(
            '<select class="form-control" id="' + name + '" name="' + name + '">'
        );
        // Add the null case first
        dropdown.append($('<option value="Not Sure">Not Sure</option>'));
        for (let i = 0; i < data.length; i++) {
            dropdown.append(
                $('<option></option>').attr('value', data[i][1]).text(data[i][1])
            );
        }
        $('#' + name).replaceWith(dropdown);
    });
}

$(document).ready(function() {
    let navListItems = $('ul.setup-panel li a');
    let navButtons = $('.setup-content a');
    let allWells = $('.setup-content');

    // If a navigation bar item is clicked and is not disabled, activate the selected panel
    navListItems.click(function(e) {
        e.preventDefault();
        let $target = $($(this).attr('href'));
        let $item = $(this).parent();

        if (!$item.hasClass('disabled')) {
            navListItems.parent().removeClass('active');
            $item.addClass('active');
            allWells.hide();
            $target.show();
        }
    });

    // When next or previous button is clicked, simulate clicking on navigation bar item
    navButtons.click(function(e) {
        let stepId = $(this).attr('href');
        // Locate the nav bar item for this step
        let $navItem = $('ul.setup-panel li a[href="' + stepId + '"]');

        $navItem.parent().removeClass('disabled');
        $navItem.trigger('click');

        e.preventDefault();
    })

    // Load the department's units and ranks when a new dept is selected
    $('#dept').on('change', function(e) {
        let deptId = $('#dept').val();
        let ranksUrl = $('#step-1').data('ranks-url');
        let unitsUrl = $('#step-1').data('units-url');
        buildSelect('rank', ranksUrl, deptId);
        buildSelect('unit', unitsUrl, deptId);

        const deptsWithUii = $('#current-uii').data('departments');
        let targetDept = deptsWithUii.find(function(element) {
            return element.id == deptId
        });

        let deptUiidLabel= targetDept.unique_internal_identifier_label
        if (deptUiidLabel) {
            $('#current-uii').text(deptUiidLabel);
        } else {
            $('#uii-question').hide();
        }

        // Disable later steps if dept changed in case ranks/units have changed
        $('ul.setup-panel li:not(.active)').addClass('disabled');
    });

    // Generate loading notification
    $('#user-notification').on('click', function(){
       $('#loader').show();
    });

    // Show/hide rank shoulder patches
    $('#show-img').on('click', function(){
       $('#hidden-img').show();
       $('#show-img-div').hide();
    });

    $('#hide-img').click(function(){
       $('#hidden-img').hide();
       $('#show-img-div').show();
    });

    // Initialize controls
    allWells.hide();
    $('#dept').trigger('change');
    $('ul.setup-panel li.active a').trigger('click');
});
