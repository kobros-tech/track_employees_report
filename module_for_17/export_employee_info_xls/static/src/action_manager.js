/** @odoo-module **/
import { registry } from "@web/core/registry";
import { standardWidgetProps } from "@web/views/widgets/standard_widget_props";
import { download } from "@web/core/network/download";
import { useService } from "@web/core/utils/hooks";

const { Component } = owl;


class PrintExcel extends Component {
    setup() {
        this.orm = useService("orm");
    }

    get showButton() {
        if (this.props.record.data.validate && 
            this.props.record.data.from_date && 
            this.props.record.data.to_date && 
            this.props.record.data.target_employees_ids.records.length > 0) {
            return false
        }
        else {
            return true
        }
    }

    async onDownloadButtonClicked() {
        // console.log(this.env.model.root.data.project_ids.records);

        const projects = this.props.record.data.project_ids.records
        const employees = this.props.record.data.target_employees_ids.records
        const employees_2 = this.props.record.data.employee_ids.records
        const from_date = this.props.record.data.from_date.c
        const to_date = this.props.record.data.to_date.c
        const validate = this.props.record.data.validate
        
        const projects_ids = projects.map((project) =>{
            let name = project.data.display_name;
            let id = project.evalContext.active_id;
            return { name, id };
        })
        const selected_employees_ids = employees_2.map((employee) =>{
            let name = employee.data.display_name;
            let id = employee.evalContext.active_id;
            return { name, id } 
        })
        const target_employees_ids = employees.map((employee) =>{
            return employee.data;
        })

        const data = { 
            "project.project": projects_ids, 
            "hr.employee": target_employees_ids,
            "employee": selected_employees_ids,
            from_date: from_date,
            to_date: to_date,
            validate: validate,
        };
        // console.log(this.props.record.data.project_ids.records)
        // console.log(data, projects_ids)
        download({
            url: '/employee_xlsx_report',
            data: { data: JSON.stringify(data) },
            error: (error) => self.call('crash_manager', 'rpc_error', error),
        });
    }
}

PrintExcel.template = "export_employee_info_xls.PrintExcel";
PrintExcel.props = {
    ...standardWidgetProps,
};
PrintExcel.fieldDependencies = [
    { name: "from_date", type: "date" },
    { name: "to_date", type: "date" },
    { name: "validate", type: "selection" },
];

const printExcel = {
    component: PrintExcel,
}

registry.category("view_widgets").add("custom_print_excel_file", printExcel);
